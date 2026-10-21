# ComfyUI workbench design

## Direction

Reference: the installed MiniMax H3 Prompt Writer's reference workspace and shell. Reuse its practical layout principles: dark work surface, input on the left, output on the right, compact controls, primary actions at the bottom. The implementation is independent and does not import the writer's code, assets or dependencies.

- Palette: canvas `#121418`, input panels `#191c22`, borders `#30353f`, text `#e7e9ee`, secondary text `#a2a8b4`, accent `#e7a07e`. The accent marks current navigation and actions, not decorative backgrounds.
- Typography: local Segoe UI/system fonts at 13px for controls and 16px for headings; Consolas/system monospace only for exported prompt text. No font downloads.
- Layout: one main navigation for Create, Library, Convert and Clip prompts. Creation pairs a 340–430px input column with an output column. Conversion uses the full panel width: settings and references above, results below, with one scroll area for the whole conversion workspace. Clip planning cards spread across available width. The panel occupies 98% of the viewport width without a desktop pixel cap. A fixed bottom action bar keeps the current action visible. Small screens retain a single column and keep the action bar reachable.
- Principles: no introduction/marketing block, duplicate branding or numbered steps; plain action labels; advanced source/reference/memory information folds away; the selected output stays readable.

```text
Storyboard    Create | Library | Convert | Clip prompts    Close
                                 API settings / diagnostics / files
Input and connection             Storyboard or video prompts
Characters / scene               Editable shots / output text
Optional settings                
                          Save and convert / Create or Convert
```

Conversion uses a different reading order: full-width model/reference/clip settings, followed by full-width prompt results. The conversion controls own one scroll area on desktop; settings and output no longer scroll independently. The original storyboard disclosure remains available above settings, and the bottom conversion action remains fixed.

## Scope and review

The design is applied by `panel/studio.css`, `panel/workbench.js` and the ComfyUI shell. The pinned shared engine and Studio assets remain unmodified. Existing controls and event handlers are moved, not reimplemented. The external create button retains its `form` association. Conversion still requires explicit consent. Save and convert saves the currently generated document as a new library copy before opening it in conversion; it does not silently regenerate changed inputs.

The first layout review removed the standalone navigation/branding from the embedded Studio to avoid two conflicting tab bars. Decorative empty-state art is hidden. Model selection stays visible; source shots, references and Ollama lifecycle controls remain available behind disclosures. Parent navigation tracks the actual inner Studio view and is disabled during active Studio operations to avoid mismatched state.

Verification uses the isolated real ComfyUI check: form submission, save-and-convert progression, selected navigation, persistent primary action, existing clip snapshots and wires, Ollama lifecycle controls, languages and mobile overflow. Test output and screenshots are ignored local artifacts. No running ComfyUI job or paid AI endpoint is used.
