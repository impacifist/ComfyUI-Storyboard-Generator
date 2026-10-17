# MiniMax H3 — conversion guide

Checked: 2026-10-11. Maintainer-authored summary, not a copy of the official manual.

Sources:
- https://github.com/MiniMax-AI/MiniMax-H3
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md
- https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/3d-animation-short-generator/SKILL.md
- https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/3d-animation-short-generator/references/shot-table-spec.md
- https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/3d-animation-short-generator/references/storyboard-guidelines.md
- https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/3d-animation-short-generator/references/model-selection.md
- https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/3d-animation-short-generator/references/qc-checklist.md

## Official guidance summary

H3 output spans four to fifteen seconds. Ref2VA accepts up to nine images; FL2VA is a different mode and must not be substituted for character references.

Base rewriting uses integrated_multimodal_description, overall_soundscape, non_diegetic_music. Reference rewriting uses subject_definitions, summary, retention_analysis, detailed_description, overall_soundscape, non_diegetic_music in that order. A Subject represents reusable content, not an asset; multiple Pictures can define one Subject. Keep picture numbering consistent. Write section descriptions in English while retaining original-language dialogue. Use [Shot 1] without a timestamp, followed by [Shot N] At MM:SS.mmm for later shots. Assign speaker IDs in vocal appearance order. Dialogue uses <d>[Language] original words</d>. Keep ambient/physical sound separate from audience-only music.

## Animation workflow guidance

The official animation skill targets MiniMax Hub and a complete stylized 3D production workflow. Its default aesthetic and Hub-specific approval/generation tools are not universal H3 prompt requirements. This converter adapts its direction guidance without adopting that workflow.

Use concrete spatial anchors, character placement, lighting continuity and timed performance beats. Base generation on the approved text storyboard; pencil panels are review aids. Keep storyboard annotations out of the rendered scene. Final review should consider identity, continuity, readable action, synchronized effects and dialogue clarity.

## Application contract

Attachment references use `<Picture 1>`, `<Picture 2>`, and so on in every instruction field, including subject definitions. The renderer canonicalizes numbered Image/Picture aliases against the actual attachment manifest; unknown attachment numbers remain errors. Original dialogue is never rewritten by this normalization.

This application supports T2VA without images and Ref2VA with character images. It does not implement frame conditioning, video/audio uploads, Context-IR API invocation or video rendering. References are attached manually in exported order; the text compiler sees metadata, not image pixels. Identity must be described using the supplied character and image notes without inventing appearance. Maintain clip-local timing and adjacent end/start states. User review remains necessary.

The H3-only system supplement is `minimax-animation-direction.md`. It preserves the selected storyboard style, structured output and renderer-owned syntax. The application keeps its existing multi-shot clips and fixed 15-second splitting; workflow suggestions do not introduce new blocking checks, automatic model switching or video retries. Whole-story events need not occur in each clip. Direction quality is prompted, not guaranteed by schema validation.
