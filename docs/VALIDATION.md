# Initial implementation validation

2026-10-17. Local source repository: `ComfyUI-Storyboard-Generator`. Initial UI integration was checked on standalone v0.5.1-beta. The shared engine/UI pin is now `c2497b28cc853c9298c03df6fd3f1c567b1840cc` (standalone v0.5.2-beta).

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

Commands: `python -m unittest discover -s tests -p "test_*.py" -q` (13 passed, including the updated engine's LM Studio unlimited socket wait), `python -m ruff check .` (passed), `node --check web/storyboard.js`, `node --check panel/bridge.js` (passed), and `python tools/test_comfy.py --comfy <installed-comfy> --python <embedded-python>` (passed on the initial integration build; not repeated for the four-line upstream timeout change).

The real ComfyUI test used temporary user/input/output directories and only this node pack. It did not restart the existing server, use its settings/library, generate images/video or call paid AI. Screenshots and sample workflow are diagnostic artifacts in ignored `storage/browser-check/`, not public release files.

Local installation is a directory junction from the user's ComfyUI `custom_nodes/ComfyUI-Storyboard-Generator` to this source repository. The already-running ComfyUI server must be restarted by the user to discover it. No public repository or release has been published as part of this implementation.
