# Ollama model release

## Design

The installed `comfyui-ollama/CompfyuiOllama.py` was inspected. Its connectivity metadata carries a keep-alive duration; generation forwards that value to the Ollama client. This integration uses the same model-lifetime concept with independent code and the standard library, without copying its implementation or adding an Ollama SDK dependency.

The [official Ollama FAQ](https://docs.ollama.com/faq#how-do-i-keep-a-model-loaded-in-memory-or-make-it-unload-immediately) documents an empty `POST /api/generate` with `model` and `keep_alive: 0` to unload a selected model. The addon sends that request only after the full successful conversion, repairs and storage commit, when explicitly enabled by the UI/request. It never unloads between internal model calls. The UI enables this option by default and remembers the user's choice locally; direct API clients default to no automatic unload unless they send `unload_ollama_after: true`.

The adapter targets the model ID used for conversion and the configured local Ollama URL, captured while the addon AI/settings lock is held. Unload shares that lock so a second addon request cannot unload a model during another addon generation. It cannot coordinate independent Ollama clients. Manual unload displays the selected target and uses the same lock and local endpoint restrictions.

Cleanup uses a 15-second socket timeout, bounded response reads, no proxy inheritance or redirects, no shell invocation, no process kill and no global VRAM purge. `done: true` plus `done_reason: unload` is required for confirmed status. Errors and unknown responses become failed/unconfirmed release status without exposing raw bodies or exception text. Saved prompts remain available even when cleanup fails. Failed conversions are left for manual unload; actual freed VRAM is not measured.

The imported engine/UI now uses upstream v0.5.4-beta, commit `0734317cb69df1ff83917c37f0c5871a450403f6`. Its source is unmodified and checksummed in `_vendor/upstream.json`. The addon routes serve diagnostics under their own namespace and retain loopback/same-origin access checks. Unload behavior lives entirely in the adapter, outside `_vendor` and outside queued snapshot nodes.

## Verification

- Unit/route tests cover the exact prompt-free request, timeout, response confirmation, malformed/oversized/error responses, local-only targets, selected-model isolation, opt-out, other providers, failed conversions, lock ownership, same-origin checks, method restrictions and saved-bundle preservation after failed cleanup.
- The isolated ComfyUI browser check exercises the real embedded UI and intercepts Ollama lifecycle calls with synthetic responses. It checks automatic opt-in/opt-out request flags, manual target, confirmation display and remembered preference, alongside the existing node/snapshot/queue/language/mobile checks.
- No actual Ollama unload, paid AI call or video generation is performed by these checks. The user's existing ComfyUI process is not restarted or modified.
