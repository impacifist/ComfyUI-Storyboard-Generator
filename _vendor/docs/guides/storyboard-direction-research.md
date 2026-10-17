# Storyboard direction research

Reviewed: 2026-10-11. Original summaries and application decisions; upstream files are not bundled or installed as executable agent instructions.

## Public skill found

[Storyboard Video Previs](https://github.com/gainubi/storyboard-video-skill/blob/main/SKILL.md) and its [shot language reference](https://github.com/gainubi/storyboard-video-skill/blob/main/references/shot-language.md) describe a beat-to-panel workflow and purpose-driven framing. This is a community skill; the repository does not establish that it represents a studio's production standard. We use it as a workflow reference, not evidence of professional authorship. Its default panel counts, storyboard-sheet image prompts, motion annotations and action-heavy defaults do not become application defaults.

## Production and teaching sources

| Source | Relevant principle | Application adaptation |
| --- | --- | --- |
| [Kyoto Animation training: layout](https://www.kyotoanimation.co.jp/school/blog/?p=79) | Camera height, subject scale, empty space and room for movement affect the intended impression. | Describe layout across the entire action, not just the opening pose. |
| [Toei Animation production process](https://corp.toei-anim.co.jp/ja/company/animation_production.html) | Storyboards communicate direction; composition and key acting drawings develop from them. | Preserve the approved direction through conversion rather than inventing camera coverage again. |
| [Pixar/Khan Academy storyboarding exercise](https://www.khanacademy.org/computing/pixar/storytelling/film-grammar/a/exercise-5-film) | Break a scene into smaller beats and visualize staging, framing and motion. | Plan attention and response beats before assigning shots. |
| [Pixar/Khan Academy film grammar](https://www.khanacademy.org/computing/pixar/storytelling/film-grammar/a/glossary-grammar) | Framing and shot size serve different viewing and emotional purposes. | Choose framing for the story point instead of cycling shot sizes. |
| [Animation Mentor: staging](https://www.animationmentor.com/blog/staging-the-12-basic-principles-of-animation/) | Placement, eyelines and screen direction help control audience attention. | Record primary subject placement and preserve spatial readability. |
| [Animation Mentor: facial animation](https://www.animationmentor.com/blog/facial-animation-101/) | A performance should reveal thought and reaction clearly; competing changes can hide the expression. | Separate recognition from response and avoid piling unrelated acting cues together. |
| [Animation Mentor: anticipation](https://www.animationmentor.com/blog/anticipation-the-12-basic-principles-of-animation/) | Preparation can be subtle as well as broad. | Match anticipation to the brief rather than requiring exaggerated poses. |

## App-specific choices and limits

Japanese 2D animation is the default creative direction requested by the user. Stable dialogue layouts, selective motion and explicit cut cues are our practical defaults, not universal studio rules. Explicit alternative styles remain supported. The generated story keeps its existing schema; camera translations in the conversion response are now separate structured fields so assembly cannot silently omit them. Source camera translation remains AI-assisted and semantic fidelity needs review.

Tests can verify camera fields reach the prompt, timing and split behavior, exact dialogue, and saved-result compatibility. They cannot establish animation quality. For an actual comparison, use the same brief, characters, reference order, generation model and settings before/after; inspect layout, eyelines, cuts, unnecessary camera drift and continuing shots across clip boundaries. No paid video generation is performed by this application or these tests.
