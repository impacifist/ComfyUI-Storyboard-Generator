"""Same-origin, loopback-only aiohttp routes under a dedicated ComfyUI namespace."""

import asyncio
import ipaddress
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlsplit

from aiohttp import web

from . import service
from .service import BusyError, ValidationError, providers, references

PREFIX = "/storyboard-generator"
ROOT = Path(__file__).resolve().parent
MAX_BODY = 16_000_000
GET_PATHS = {"/config", "/guides", "/example", "/catalog", "/diagnostics"}
POST_PATHS = {"/settings", "/generate", "/generation/accept", "/validate", "/review", "/export", "/library/list", "/library/save",
              "/library/load", "/library/delete", "/library/restore", "/references/upload", "/references/save",
              "/conversion/plan", "/conversion/compile", "/ollama/unload", "/diagnostics/clear"}


def allowed(request):
    try:
        if not ipaddress.ip_address(request.remote or "").is_loopback:
            return False
        host = urlsplit("//" + request.host).hostname
        if host not in ("localhost", "127.0.0.1", "::1"):
            return False
        origin = request.headers.get("Origin")
        if origin and origin != f"{request.scheme}://{request.host}":
            return False
        return request.headers.get("Sec-Fetch-Site") != "cross-site"
    except ValueError:
        return False


def response(data, status=200):
    return web.Response(text=json.dumps(data, ensure_ascii=False, allow_nan=False), status=status,
                        content_type="application/json", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


async def api_route(request):
    if not allowed(request):
        return response({"error": "Storyboard is available only from this computer and the same ComfyUI origin."}, 403)
    path = "/" + request.match_info["path"]
    try:
        payload = None
        if request.method == "POST":
            if path not in POST_PATHS:
                raise LookupError()
            if request.content_type != "application/json":
                return response({"error": "JSON requests only."}, 415)
            limit = 6_800_000 if path == "/references/upload" else MAX_BODY
            if request.content_length is not None and request.content_length > limit:
                return response({"error": "Request too large."}, 413)
            content = bytearray()
            async for chunk in request.content.iter_chunked(65536):
                content.extend(chunk)
                if len(content) > limit:
                    return response({"error": "Request too large."}, 413)
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValidationError("JSON object required.")
        else:
            if path.startswith("/references/image/"):
                asset = await asyncio.to_thread(references.asset, path.rsplit("/", 1)[-1])
                return web.Response(body=asset["data"], content_type=asset["mime"], headers={"Cache-Control": "no-store"})
            if path.startswith("/conversion/package/"):
                data = await asyncio.to_thread(references.package, path.rsplit("/", 1)[-1])
                return web.Response(body=data, content_type="application/zip", headers={"Cache-Control": "no-store"})
            if path not in GET_PATHS and not path.startswith("/bundle/"):
                raise LookupError()
        result = await asyncio.to_thread(service.dispatch, path, payload)
        return response(result)
    except LookupError:
        return response({"error": "Not found."}, 404)
    except BusyError as error:
        return response({"error": str(error)}, 409)
    except (ValidationError, json.JSONDecodeError, UnicodeError, ValueError) as error:
        message = str(error) if isinstance(error, ValidationError) else "Invalid request or clip data."
        return response({"error": message}, 400)
    except providers.ProviderError as error:
        return response({"error": str(error)}, 502)
    except Exception:
        # No raw exception: provider errors may contain user text or credentials.
        logging.getLogger(__name__).warning("Storyboard request failed; private error details suppressed")
        return response({"error": "Unable to complete the request. Saved projects remain unchanged."}, 500)


async def studio_route(request):
    if not allowed(request):
        return response({"error": "Local access only."}, 403)
    asset = request.match_info.get("asset", "") or "index.html"
    files = {"index.html": "text/html", "app.js": "text/javascript", "i18n.js": "text/javascript",
             "translations.js": "text/javascript", "style.css": "text/css", "bridge.js": "text/javascript", "diagnostics.js": "text/javascript",
             "workbench.js": "text/javascript", "studio.css": "text/css"}
    if asset not in files:
        return response({"error": "Not found."}, 404)
    path = ROOT / "panel" / asset if asset in ("bridge.js", "workbench.js", "studio.css") else service.VENDOR / "web" / asset
    text = path.read_text(encoding="utf-8")
    if asset == "index.html":
        for name in ("style.css", "translations.js", "i18n.js", "app.js", "diagnostics.js"):
            text = text.replace('"/' + name + '"', '"' + PREFIX + '/studio/' + name + '"')
        text = text.replace("</head>", f'<link rel="stylesheet" href="{PREFIX}/studio/studio.css"><script src="{PREFIX}/studio/bridge.js" defer></script><script src="{PREFIX}/studio/workbench.js" defer></script></head>')
        text = text.replace("<title>Persona Storyboard</title>", "<title>Storyboard Studio</title>")
    if asset in ("app.js", "diagnostics.js"):
        text = text.replace("/api/", PREFIX + "/api/")
    if asset == "i18n.js":
        text = text.replace("persona-storyboard.ui-language", "comfyui-storyboard.ui-language")
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
               "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
               "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'"}
    return web.Response(text=text, content_type=files[asset], headers=headers)


def register(server):
    if getattr(server, "_storyboard_generator_registered", False):
        return
    import folder_paths

    data = os.environ.get("STORYBOARD_DATA_DIR") or str(Path(folder_paths.get_user_directory()) / "storyboard-generator")
    service.configure(data)
    server.routes.get(PREFIX + "/studio/")(studio_route)
    server.routes.get(PREFIX + "/studio/{asset}")(studio_route)
    server.routes.get(PREFIX + "/api/{path:.*}")(api_route)
    server.routes.post(PREFIX + "/api/{path:.*}")(api_route)
    server._storyboard_generator_registered = True
