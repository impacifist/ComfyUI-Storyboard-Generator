# Public beta validation

2026-10-17. Repository: https://github.com/impacifist/ComfyUI-Storyboard-Generator. The shared engine/UI pin is `0734317cb69df1ff83917c37f0c5871a450403f6` (standalone v0.5.4-beta); all 34 imported file checksums were verified before the first release.

| Requirement | Evidence |
| --- | --- |
| ComfyUI integration loads | Isolated installed ComfyUI 0.41.1 with official frontend 1.55.17 registered `StoryboardClipPrompt` and namespaced routes. |
| Top icon opens creation panel | Real Chromium clicked the Storyboard action-bar button and opened the embedded Studio. |
| Create inside panel | Real Studio template demo produced and saved a storyboard in temporary storage. |
| Separate clip prompts | Mock-converted 45-second source to 3 user-set 13-second clips; panel search and all 3 output nodes checked. |
| Avoid confusing/duplicate clips | Project and conversion selection, unique version labels, source-shot/scene summary, exact-identity deduplication and connected/other-version status. |
| Explicit update, keep wires | A second conversion left nodes unchanged until update was selected; existing prompt connection survived. |
| Assign clip from a node | Choose clip selected C03 for an existing node, retaining the node and its wire. |
| Portable workflow | Serialized workflow reloaded the same snapshot. Real ComfyUI queued the snapshot node into PreviewAny and returned the exact prompt. |
| No AI call during queue | Node implementation has no provider/library dependency; mocked-provider guard in unit tests and string-only real queue. |
| Three UI languages and mobile | English/Korean/Japanese wrapper labels checked through the embedded Studio language switch; 390px layout checked without panel overflow. |
| Local API boundaries | Unit tests cover cross-origin/host/nonloopback rejection, JSON shape/content type/size, method restrictions, redacted failures and busy state. |
| Snapshot integrity | Unit tests cover invalid identities/durations, altered content, disallowed fields, deleted source project and distinct conversion hashes. |
| Upstream integrity | Every vendored file matches its pinned manifest checksum. |

Commands: `python -m unittest discover -s tests -p "test_*.py" -q` (21 passed), `ruff check .` (passed), and `node --check` for `web/storyboard.js`, `panel/bridge.js` and `panel/workbench.js` (passed). `python tools/test_comfy.py --comfy <installed-comfy> --python <embedded-python>` passed before release and again when capturing README screenshots. The browser check covers desktop/mobile, three UI languages, creation, clip search, deduplication, explicit updates, preserved wires, workflow reload, real STRING queue execution and mocked Ollama unload requests.

The real ComfyUI test used temporary user/input/output directories and only this node pack. It did not restart the existing server, use its settings/library, generate images/video or call paid AI. Storyboards use the built-in demo template and conversion responses are mocked. Selected screenshots are published under `docs/images/`; raw logs and diagnostic artifacts remain ignored under `storage/browser-check/`.

The first public prerelease is `v0.1.0-beta`. Installation requires restarting ComfyUI and refreshing the browser. These checks establish UI and integration behavior, not AI output quality, real Ollama VRAM release or compatibility with every ComfyUI version.
