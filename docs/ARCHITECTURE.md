# ComfyUI integration

## Contract

Outcome: create/edit/convert storyboards in a ComfyUI panel and emit independent clip prompt strings.

Scope: this independent node pack, its isolated private data and local development checks. The standalone repository and the user's running ComfyUI/video workflow are unchanged. Public GitHub publication is not part of initial implementation.

Done when: real ComfyUI opens the panel, the embedded Studio works, clips become distinct connected nodes, snapshots survive workflow reload, updates preserve wires, and queue execution returns the exact saved string without AI calls.

## Components

- `_vendor/`: unmodified upstream engine, guides, example and Studio assets pinned by commit and per-file checksum.
- `service.py`: invokes that engine with separate library/settings roots and a process-wide nonblocking AI/settings lock.
- `ollama_memory.py`: sends a bounded local unload request for one selected model; `service.py` owns the lifecycle after a complete, saved conversion. Release status is separate from saved prompt data. No LLM request is added to node execution. `panel/bridge.js` owns the persisted checkbox and manual action, outside the unmodified snapshot. See [Ollama memory release](OLLAMA_MEMORY.md).
- `routes.py`: aiohttp routes on ComfyUI's existing server under `/storyboard-generator`, loopback/same-origin guards, bounded JSON requests, redacted errors and worker-thread execution for blocking engine calls.
- `panel/bridge.js`: same-origin iframe bridge. Only conversion IDs, project IDs and UI language are passed between frames; never keys. API and asset paths are namespaced when serving upstream assets; the snapshot files are not modified.
- `web/storyboard.js`: action-bar/menu entrypoint, persistent native dialog, clip version picker, search, selection, node creation and explicit updates.
- `panel/workbench.js`, `panel/studio.css`: ComfyUI-only layout adapter, unified navigation synchronization, input/output layout, form-associated fixed action bar and explicit save-and-convert flow. Display changes do not modify the pinned engine. See [design notes](DESIGN_COMFYUI.md).
- `clip_snapshot.py`: strict, versioned, credential-free snapshot schema with identity and checksum.
- `nodes.py`: deterministic STRING/FLOAT/STRING outputs. No database or provider access during execution.

## Version and connection semantics

A clip key is `(board_id, conversion_id, clip_id)`. Node insertion skips exact duplicates within the active graph. A node update is explicit and preserves its ID and connections. Bulk updates additionally require identical source-shot lists; otherwise the user must reassign the node. Deleted local projects do not invalidate saved node snapshots. Snapshots remain readable across machines.

All graph operations apply to the active canvas graph. The panel captures the graph when opened; applying clips after switching graphs is rejected. Workflow serialization stores the snapshot in a normal STRING widget and the metadata in node properties. It does not depend on transient JavaScript maps or local library IDs alone.

## Design

The wrapper uses a slate-blue editing palette: paper `#f4f7fb`, text `#24334b`, borders `#d4ddea`, action `#315fa8`, muted text `#627087`, white work surfaces. Segoe UI/system UI matches a desktop editing tool. A broad modal keeps the existing editor spacious; the clip view uses aligned rows, a fixed footer and searchable source-shot metadata rather than many output sockets on one node. Version selection and connection status carry the information needed to avoid confusing clips. The iframe isolates the existing app's styles from ComfyUI.

## Limits

No remote/multi-user adapter, visual analysis, IMAGE tensor output, video API submission, workflow timing/frame-context corrections or automatic concatenation. No automatic prompt regeneration or node updates during queue execution. Older or newer ComfyUI frontend compatibility is not inferred from one tested version.

The core package is not currently published separately, so the initial integration vendors a tracked upstream revision. Updates are explicit and refuse edited vendor files. Moving to a separately versioned engine dependency is a future packaging change; it is not required to start ComfyUI or use this implementation.

## Primary interface references

- [ComfyUI JavaScript extensions](https://docs.comfy.org/custom-nodes/js/javascript_overview)
- [Commands and topbar menus](https://docs.comfy.org/custom-nodes/js/javascript_topbar_menu)
- [Dialog API](https://docs.comfy.org/custom-nodes/js/javascript_dialog)
- [Backend node properties](https://docs.comfy.org/custom-nodes/backend/server_overview)
- `actionBarButtons` was checked against the installed official frontend package 1.55.17 (`ActionBarButtons` and the built-in feedback-button extension), beyond the menu API documented above.
