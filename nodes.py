"""Snapshot outputs are deterministic and never invoke a model on queue execution."""

from .clip_snapshot import decode_snapshot


class StoryboardClipPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"clip_data": ("STRING", {"default": "", "multiline": True})}}

    RETURN_TYPES = ("STRING", "FLOAT", "STRING")
    RETURN_NAMES = ("prompt", "duration_seconds", "clip_id")
    FUNCTION = "output_clip"
    CATEGORY = "Storyboard"
    DESCRIPTION = "Choose a generated clip in the Storyboard panel. Outputs its saved prompt without an AI call."

    def output_clip(self, clip_data):
        clip = decode_snapshot(clip_data)
        return (clip["prompt"], float(clip["duration"]), clip["clip_id"])

    @classmethod
    def VALIDATE_INPUTS(cls, clip_data):
        try:
            decode_snapshot(clip_data)
        except ValueError as error:
            return str(error)
        return True


NODE_CLASS_MAPPINGS = {"StoryboardClipPrompt": StoryboardClipPrompt}
NODE_DISPLAY_NAME_MAPPINGS = {"StoryboardClipPrompt": "Storyboard Clip Prompt"}
