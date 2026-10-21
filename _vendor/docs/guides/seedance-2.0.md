# Seedance 2.0 — conversion guide

Checked: 2026-10-10. Maintainer-authored summary, not a copy of the official manual.

Sources:
- https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide
- https://docs.byteplus.com/en/docs/modelark/video-generation-tutorial
- https://docs.byteplus.com/en/docs/byteplus_las/video_gen_enhanced

## Official guidance summary

Identify subjects and specify what each numbered image contributes. Image numbering follows attachment order. For character identity, prefer a separate headshot and full-body image; combined multi-view character sheets can confuse identity. Put important references first. Describe actions, camera, environment and audio concretely. Dialogue uses braces, sound effects angle brackets and music parentheses. Explicitly mark dialogue language when it is neither Chinese nor English. Image-reference generation accepts up to nine images. Seedance 2.0 durations are whole seconds from four through fifteen. Other versions and deployment surfaces may differ.

## Application contract

Speaker binding updated: 2026-10-21. The renderer owns each original line's character identity and, when available, includes that character's ordered Image references directly in its attribution. Structured cues must copy the original speaker ID and distinguish visible speech, off-screen speech and approved voiceover. Other characters listen without lip-syncing that line. These are application safeguards; they do not guarantee the video model follows the prompt. H3 Subject/speaker tags are not used in Seedance output.

This application handles text-only generation and character image reference generation, not video editing, extension or first/last-frame conditioning. Preserve the approved storyboard and original dialogue. Use the supplied attachment manifest literally. User notes explain intended reference use; this compiler does not inspect image pixels. Each clip is independently usable with the same ordered reference bundle. Timing must fit the requested duration. Never promise identical output or automatic seamless stitching. Hosting and actual video submission remain outside this application.
