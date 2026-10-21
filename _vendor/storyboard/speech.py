"""Source-owned dialogue identity shared by every video prompt renderer."""

import re

from .schema import TEXT, ValidationError, obj

CUE = obj(speaker=TEXT, mode={"type": "string", "enum": ["on_screen", "off_screen", "voiceover", "unspecified"]}, onset=TEXT)


def bindings(document, names, assets=()):
    return [{"speaker": c["id"], "label": names[c["id"]], "subject": f"<Subject {i}>",
             "pictures": [a["label"] for a in assets if a["character_id"] == c["id"] and a["role"] != "environment"]}
            for i, c in enumerate(document["brief"]["characters"], 1)]


def replace_labels(value, mapping):
    # One pass avoids recursively replacing a label contained in another label.
    pattern = r"(?<![\w])(?:" + "|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)) + r")(?![\w])"
    return re.sub(pattern, lambda match: mapping[match[0]], value) if mapping else value


def reference_prose(draft, identities):
    """Bind AI-only prose to canonical subjects, never touch source dialogue."""
    mapping = {item["label"]: item["subject"] for item in identities}

    def visit(value, key=""):
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, key) for v in value]
        if isinstance(value, str) and key not in {"id", "speaker", "character_id", "holder", "name", "subject_definitions"}:
            return replace_labels(value, mapping)
        return value

    return visit(draft)


def prose_labels(names):
    labels = {key: re.sub(r" \[[A-Za-z0-9_-]+\]$", "", label) for key, label in names.items()}
    original = list(labels.values())
    for index, (key, label) in enumerate(list(labels.items()), 1):
        if original.count(label) > 1:
            labels[key] = f"{label} (Character {index})"
    return labels


def validate_cues(directed, planned, identities, path):
    lines, cues = planned["source"]["dialogue"], directed["speech_cues"]
    if len(cues) != len(lines):
        raise ValidationError(f"{path}.speech_cues: one cue per source dialogue line required")
    for index, (line, cue) in enumerate(zip(lines, cues)):
        prefix = f"{path}.speech_cues[{index}]"
        if cue["speaker"] != line["speaker"]:
            raise ValidationError(f"{prefix}.speaker: must match source.dialogue[{index}].speaker exactly")
        if not cue["onset"].strip():
            raise ValidationError(f"{prefix}.onset: nonempty English performance cue required")
        # Cues describe the assigned speaker's own performance, not a second cast
        # list. Other characters' actions belong in direction/layout. Checking
        # explicit canonical identities avoids guessing actors from pronouns.
        for identity in identities:
            if identity["speaker"] == line["speaker"]:
                continue
            aliases = [identity["label"], identity["subject"]]
            for alias in aliases:
                if re.search(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", cue["onset"], re.IGNORECASE):
                    raise ValidationError(f"{prefix}.onset: describe only the assigned speaker; move other character actions to direction")


def performance(actor, cue):
    return f"Speech onset for {actor}: {cue['onset'].rstrip(' .')}."


def speech_verb(cue):
    return {"on_screen": "says on screen", "off_screen": "says off-screen",
            "voiceover": "says in an off-screen voiceover", "unspecified": "says"}[cue["mode"]]


def listeners(actor, cue):
    text = f"Only {actor} delivers this line; the other characters listen without speaking or lip-syncing it."
    if cue["mode"] == "voiceover":
        text = f"{actor}'s on-screen lips remain completely closed. " + text
    elif cue["mode"] == "off_screen":
        text += " The speaker remains outside the frame; visible listeners do not mouth the off-screen words."
    return text
