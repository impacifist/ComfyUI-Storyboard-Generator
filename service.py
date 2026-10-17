"""ComfyUI adapter for the pinned engine. Private data is isolated from the web app."""

import json
import threading
from pathlib import Path

from ._vendor.storyboard import conversion, diagnostics, engine, guides, library, providers, references
from ._vendor.storyboard.schema import ValidationError, validate_brief
from .clip_snapshot import make_bundle
from .ollama_memory import unload_model

VENDOR = Path(__file__).resolve().parent / "_vendor"
BUSY = threading.Lock()
SERIAL_OPERATIONS = {"/settings", "/generate", "/review", "/conversion/compile", "/ollama/unload"}


class BusyError(Exception):
    pass


def configure(data_directory):
    library.ROOT = Path(data_directory)
    providers.ROOT = Path(data_directory)


def dispatch(path, payload=None):
    if path not in SERIAL_OPERATIONS:
        return operation(path, payload)
    if not BUSY.acquire(blocking=False):
        raise BusyError("Another generation or settings operation is running. Please wait.")
    scope = diagnostics.begin_operation("/api" + path)
    try:
        auto_unload = False
        if path == "/conversion/compile" and isinstance(payload, dict):
            payload = dict(payload)
            auto_unload = payload.pop("unload_ollama_after", False)
            if type(auto_unload) is not bool:
                raise ValidationError("Auto unload must be true or false.")
        # Capture the configured target while settings changes are locked out.
        base = providers.ollama_url(providers.load_settings().get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")) if auto_unload and payload.get("provider") == "ollama" else None
        result = operation(path, payload)
        if base:
            result["ollama_release"] = unload_model(base, payload.get("model"))
        return result
    finally:
        diagnostics.end_operation(scope)
        BUSY.release()


def operation(path, payload):
    if payload is None:
        if path == "/config":
            return providers.configuration()
        if path == "/diagnostics":
            return diagnostics.listing()
        if path == "/guides":
            return {"guides": guides.catalog()}
        if path == "/example":
            return json.loads((VENDOR / "examples/rainy-classroom.json").read_text(encoding="utf-8"))
        if path == "/catalog":
            projects = []
            for board in library.listing():
                entries = library.conversions(board["id"])
                projects.append({**board, "conversions": [{"id": entry["id"], "created_at": entry["created_at"],
                    "target_model": entry["result"]["target_model"],
                    "clips": len(entry["result"]["output"]["clips"])} for entry in entries]})
            return {"projects": projects}
        if path.startswith("/bundle/"):
            with library.database() as db:
                row = db.execute("SELECT board_id,result FROM conversions WHERE id=?", (library.identifier(path.rsplit("/", 1)[-1]),)).fetchone()
            if row is None:
                raise ValidationError("Conversion not found. Generate prompts in the Studio first.")
            return make_bundle(row["board_id"], library.load(row["board_id"]), path.rsplit("/", 1)[-1], json.loads(row["result"]))
    else:
        if path == "/diagnostics/clear":
            diagnostics.clear_completed()
            return diagnostics.listing()
        if path == "/ollama/unload":
            base = providers.ollama_url(providers.load_settings().get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
            return {"ollama_release": unload_model(base, payload.get("model"))}
        if path == "/settings":
            return providers.save_settings(payload)
        if path == "/generate":
            document = engine.generate(payload)
            return {"document": document, "review": engine.review(document)}
        if path == "/validate":
            if "document" in payload:
                return {"review": engine.review(payload["document"])}
            validate_brief(payload.get("brief"))
            return {"valid": True}
        if path == "/review":
            return {"ai_review": engine.semantic_review(payload.get("document"), payload.get("provider"), payload.get("model", ""))}
        if path == "/export":
            return {"markdown": engine.markdown(payload.get("document"))}
        if path == "/library/list":
            return {"items": library.listing(payload.get("deleted", False))}
        if path == "/library/save":
            return {"saved": library.save(payload.get("document"))}
        if path == "/library/load":
            key = payload.get("id")
            document = library.load(key)
            return {"document": document, "review": engine.review(document), "conversions": library.conversions(key), "references": references.load(key)}
        if path in ("/library/delete", "/library/restore"):
            library.trash(payload.get("id"), path.endswith("/delete"))
            return {"ok": True}
        if path == "/references/upload":
            return {"asset": references.upload(payload)}
        if path == "/references/save":
            return {"references": references.save(payload.get("id"), payload.get("references"))}
        if path == "/conversion/plan":
            return {"plan": conversion.preflight(library.load(payload.get("id")), payload)[0]}
        if path == "/conversion/compile":
            result = conversion.compile_prompts(library.load(payload.get("id")), payload)
            saved_id = library.save_conversion(payload.get("id"), result)
            if result.get("references"):
                references.save(payload.get("id"), payload.get("references", []))
            return {"result": result, "id": saved_id}
    raise LookupError("Route not found")
