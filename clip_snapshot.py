"""Portable immutable clip identities. No file access, credentials or provider calls."""

import hashlib
import json
import math
import re

FIELDS = {"version", "board_id", "conversion_id", "clip_id", "title", "summary", "target_model",
          "duration", "prompt", "source_shots", "revision"}


def digest(value):
    content = {key: item for key, item in value.items() if key != "revision"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def validate_snapshot(value):
    if not isinstance(value, dict) or set(value) != FIELDS or type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Select a clip from the Storyboard panel; unsupported clip snapshot.")
    for key in ("board_id", "conversion_id"):
        if not isinstance(value[key], str) or not re.fullmatch(r"[a-f0-9]{32}", value[key]):
            raise ValueError("Invalid project or conversion identity.")
    if not isinstance(value["clip_id"], str) or not re.fullmatch(r"C\d{2,6}", value["clip_id"]):
        raise ValueError("Invalid clip identity.")
    for key, limit in (("title", 12000), ("summary", 12000), ("target_model", 200), ("prompt", 2_000_000)):
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > limit:
            raise ValueError("Invalid clip " + key)
    if (type(value["duration"]) not in (int, float) or not math.isfinite(value["duration"])
            or not 0 < value["duration"] <= 15):
        raise ValueError("Clip duration must be greater than zero and at most 15 seconds.")
    if (not isinstance(value["source_shots"], list) or not value["source_shots"]
            or any(not isinstance(s, str) or not re.fullmatch(r"S\d{2,6}", s) for s in value["source_shots"])):
        raise ValueError("Invalid source shot manifest.")
    if value["revision"] != digest(value):
        raise ValueError("The clip snapshot changed. Select the approved clip again in the panel.")
    return value


def encode_snapshot(value):
    validate_snapshot(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def decode_snapshot(encoded):
    if not isinstance(encoded, str) or len(encoded.encode("utf-8")) > 8_000_000:
        raise ValueError("Clip snapshot is missing or too large. Select a clip in the panel.")
    try:
        value = json.loads(encoded)
    except (ValueError, UnicodeError):
        raise ValueError("Select a clip in the Storyboard panel before running this node.") from None
    return validate_snapshot(value)


def make_bundle(board_id, document, conversion_id, result):
    if result.get("output_language") != "english_except_dialogue":
        raise ValueError("Reconvert this storyboard using the English instruction rules first.")
    plan = {clip["id"]: clip for clip in result["plan"]["clips"]}
    clips = []
    for output in result["output"]["clips"]:
        clip = plan[output["id"]]
        ids = list(dict.fromkeys(s["id"] for s in clip["shots"]))
        summary = " / ".join(s["source"].get("purpose") or s["id"] for s in clip["shots"])
        value = {"version": 1, "board_id": board_id, "conversion_id": conversion_id,
                 "clip_id": clip["id"], "title": document["brief"]["title"], "summary": summary[:12000],
                 "target_model": result["target_model"], "duration": clip["duration"],
                 "source_shots": ids, "prompt": output["prompt"]}
        value["revision"] = digest(value)
        clips.append(validate_snapshot(value))
    return {"board_id": board_id, "conversion_id": conversion_id, "clips": clips}
