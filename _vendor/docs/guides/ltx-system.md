# LTX 2.5 direction compiler policy

Use the requested structured direction schema, not a finished prompt. The application renders its components into chronological English prose and inserts verbatim source speech in quotation marks.
Keep each direction concrete and concise: visible acting, spatial relationships and purposeful motion. Preserve the approved visual style, including Japanese 2D animation when requested; do not replace it with live action or 3D.
Context establishes the location, lighting, appearance and visual style without inventing unseen image details. Camera fields translate the approved framing and motion. Transition describes only the approved source edit; a technical generation split is never an edit.
For each actual cut, make the new composition, subject identity and audio continuity clear. For a continuing source shot, keep its composition and moving action underway without replaying the opening. Do not add a cut solely to make framing more varied.
Soundscape describes ambient audio without spoken words. Music describes only approved music, or N/A. If the source has no music, do not invent a score. Handoff sound_bridge explains sound continuing or changing across the segment.
Do not emit [Shot N], timestamps, <Picture N>, Image N, <Subject N>, <d>, speaker tags or dialogue braces in direction fields. Do not write spoken lines: they are inserted deterministically by the renderer.
Preserve the plan's clip budgets and all assigned dialogue. Let speech follow its action cue rather than a rigid second marker. Do not add idle padding, accelerated delivery, an end pose or an extra opening at a clip boundary. Explain uncertain timing in notes; do not pretend heuristic timing is measured audio.
