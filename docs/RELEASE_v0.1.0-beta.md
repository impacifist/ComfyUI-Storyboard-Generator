# v0.1.0-beta

First public beta of ComfyUI Storyboard Generator.

- Create, edit and save storyboards with 1–5 character personas in a ComfyUI panel.
- Convert storyboards into MiniMax H3 or Seedance prompts with adjustable clip splitting.
- Add clip prompts as STRING nodes with duration and clip identity outputs; preserve saved prompts and wires across workflow reloads.
- Configure OpenAI, Claude, Ollama, LM Studio or OpenAI-compatible providers in the panel.
- Optionally unload the selected Ollama model after successful prompt conversion.
- English, Korean and Japanese interfaces; TXT, JSON and ZIP exports.

Install the repository under `ComfyUI/custom_nodes/ComfyUI-Storyboard-Generator`, restart ComfyUI and refresh the browser. See the README for setup.

This beta targets local, single-user access and was tested with ComfyUI 0.41.1 / frontend 1.55.17. API settings are stored locally in plaintext. Reference images must be attached to video-generation nodes separately. The addon does not render or concatenate videos. Automated generation checks use mocked AI responses, not paid services or actual model inference.
