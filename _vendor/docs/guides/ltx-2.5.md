# LTX 2.5 — reviewed prompt guide

Reviewed: 2026-10-18. This is an application-specific summary, not a copy of the official documentation.

## Official sources

- https://docs.ltx.io/open-source-model/usage-guides/prompting-guide/
- https://ltx.io/blog/ltx-2-5-prompt-guide
- https://docs.ltx.io/open-source-model/usage-guides/image-to-video
- https://docs.ltx.io/open-source-model/usage-guides/text-to-video

## Prompt construction

Describe the scene as a chronological sequence of concrete actions. Include framing, environment, lighting, identifiable characters, camera motion and audible events. Show emotion through performance. Use present-tense prose and keep spoken lines in quotation marks with their speaker and language.

For a continuous take, describe movement within one coherent composition. For multiple shots, name each actual transition in prose, establish the new framing and recurring subjects, and explain what happens to the sound across the edit. The official guide suggests 2–4 shots per generation; this is advice, not a mandatory limit. Preserve the approved storyboard instead of adding cuts or removing shots to satisfy a recommendation.

Avoid importing another model's attachment tags or numbered shot-list syntax. Supply a readable narrative rather than a technical timing checklist. Include pauses only when they are part of the approved performance.

## Starting from an image

The opening frame provides the initial appearance and composition. Concentrate the supporting prompt on what moves, how the camera behaves and what is heard. An uninterrupted take is usually appropriate unless the storyboard intentionally cuts away.

The official ComfyUI image-to-video template takes its source through LoadImage. Its frame count follows 8n+1; at 24 fps, 97 frames are approximately four seconds. Configure the actual length and frame rate in the video workflow. The optional prompt enhancer rewrites text; disable it when testing the generator's exact wording.

## Application contract

Speaker binding updated: 2026-10-21. The application binds each quoted line and its performance cue to the exact original speaker. It writes the character identity immediately before speech, distinguishes visible/off-screen speech and approved voiceover, and keeps listeners from lip-syncing another character's words. This is an application safeguard, not a guarantee of generated video performance. H3 Subject/speaker tags are never imported into LTX prose.

The 4–15-second planner range is this application's current policy, not a claimed LTX model maximum. Start images are connected separately for each clip; this release does not transfer images into LTX nodes or provide multi-image identity conditioning. The converter cannot inspect an opening image. Use reference notes and the approved storyboard as descriptive context only.

Original dialogue is inserted by the application, never rewritten by the conversion LLM. All other rendered instructions remain English. Clip splits preserve the existing handoff and shared-state contracts, without exposing their internal IDs as shot directions. A new generation request must not introduce an automatic pause, scene ending or camera reset.

This release prepares prompts, not video jobs, Dub-It dubbing or IC-LoRA editing. Prompt preparation does not guarantee speech accuracy, timing, identity consistency or seamless video joins; verify the actual output with the selected workflow.
