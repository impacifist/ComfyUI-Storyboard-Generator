"""ComfyUI entrypoint. No HTTP server or AI call is started by importing nodes."""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

try:
    from server import PromptServer
except ImportError:
    PromptServer = None

if PromptServer is not None and getattr(PromptServer, "instance", None) is not None:
    from .routes import register

    register(PromptServer.instance)

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
