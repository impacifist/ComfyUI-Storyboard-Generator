"""Release one selected local Ollama model; never purge other models or ComfyUI."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from ._vendor.storyboard.providers import NoRedirect, ollama_url
from ._vendor.storyboard.schema import ValidationError


def unload_model(base, model):
    base = ollama_url(base)
    if not isinstance(model, str) or not model.strip() or len(model) > 200 or any(ord(c) < 32 for c in model):
        raise ValidationError("Enter the Ollama model ID to unload.")
    request = Request(base + "/api/generate", method="POST", headers={"Content-Type": "application/json"},
                      data=json.dumps({"model": model.strip(), "stream": False, "keep_alive": 0}).encode())
    # Cleanup must not leave a completed conversion waiting indefinitely.
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            return {"status": "failed"}
        value = json.loads(raw)
        if isinstance(value, dict) and value.get("done") is True and value.get("done_reason") == "unload":
            return {"status": "unloaded"}
        return {"status": "unconfirmed"}
    except (HTTPError, URLError, OSError, ValueError):
        # Never expose server error bodies, URLs or raw exception text.
        return {"status": "failed"}
