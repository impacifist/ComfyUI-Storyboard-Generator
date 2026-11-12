"""Complete missing off-screen character states during story generation only.

The pinned engine requires each shot's start_state and end_state to contain an
entry for every character in the brief. Models often omit characters that are
off-screen in one or more shots, which aborts an otherwise usable storyboard.
This adapter fills those entries from the previous shot (or a neutral off-screen
state) before the strict vendor validation runs.

Stored documents are still validated exactly; repair is enabled only around a
generation request in service.dispatch.
"""

import copy
from contextvars import ContextVar

from ._vendor.storyboard import batch_generation, engine
from ._vendor.storyboard.schema import validate_story as _vendor_validate_story

ACTIVE = ContextVar("storyboard_generation_state_repair", default=False)
FIELDS = ("position", "pose", "gaze", "emotion")
NEUTRAL = {"position": "화면 밖", "pose": "대기", "gaze": "화면 밖", "emotion": "차분함"}
NOTE_PREFIX = "누락된 인물 상태 자동 보완: "


def _clean_entry(entry):
    if not isinstance(entry, dict):
        return None
    character_id = entry.get("character_id")
    if not isinstance(character_id, str) or not character_id.strip():
        return None
    cleaned = {"character_id": character_id}
    for field in FIELDS:
        value = entry.get(field)
        cleaned[field] = value if isinstance(value, str) and value.strip() else ""
    return cleaned


def _entries(state):
    if not isinstance(state, dict) or not isinstance(state.get("characters"), list):
        return None, False
    by_id = {}
    changed = False
    for entry in state["characters"]:
        cleaned = _clean_entry(entry)
        if cleaned is None or cleaned["character_id"] in by_id:
            changed = True
            continue
        by_id[cleaned["character_id"]] = cleaned
    return by_id, changed


def _fill(by_id, ids, inherited, sibling):
    result = {}
    changed = bool(set(by_id) - set(ids))
    for character_id in ids:
        entry = by_id.get(character_id)
        if entry is None:
            sources = (inherited.get(character_id), sibling.get(character_id))
            entry = {"character_id": character_id}
            for field in FIELDS:
                value = next((source.get(field) for source in sources
                              if isinstance(source, dict)
                              and isinstance(source.get(field), str)
                              and source.get(field).strip()), "")
                entry[field] = value or NEUTRAL[field]
            changed = True
        else:
            entry = copy.deepcopy(entry)
            sources = (inherited.get(character_id), sibling.get(character_id))
            for field in FIELDS:
                if entry[field]:
                    continue
                value = next((source.get(field) for source in sources
                              if isinstance(source, dict)
                              and isinstance(source.get(field), str)
                              and source.get(field).strip()), "")
                entry[field] = value or NEUTRAL[field]
                changed = True
        result[character_id] = entry
    return result, changed


def _complete_shot(shot, ids, previous_end):
    start_state, end_state = shot.get("start_state"), shot.get("end_state")
    start_raw, start_changed = _entries(start_state)
    end_raw, end_changed = _entries(end_state)
    if start_raw is None or end_raw is None:
        return False, previous_end

    start, start_filled = _fill(start_raw, ids, previous_end, end_raw)
    end, end_filled = _fill(end_raw, ids, start, previous_end)
    start_state["characters"] = [start[character_id] for character_id in ids]
    end_state["characters"] = [end[character_id] for character_id in ids]
    return start_changed or end_changed or start_filled or end_filled, end


def complete_states(story, brief):
    """Fill missing character states in place; return whether anything changed."""
    try:
        if not isinstance(story, dict) or not isinstance(story.get("shots"), list):
            return False
        ids = [character["id"] for character in brief.get("characters", [])
               if isinstance(character, dict) and isinstance(character.get("id"), str)
               and character["id"].strip()]
        if not ids:
            return False

        previous_end = {}
        changed_shots = []
        for shot in story["shots"]:
            if not isinstance(shot, dict):
                continue
            changed, previous_end = _complete_shot(shot, ids, previous_end)
            if changed:
                changed_shots.append(str(shot.get("id", "")))

        if not changed_shots:
            return False
        labeled = ", ".join(changed_shots[:8])
        if len(changed_shots) > 8:
            labeled += f" 외 {len(changed_shots) - 8}개 컷"
        note = (f"{NOTE_PREFIX}{labeled}. 이전 컷 또는 화면 밖 기준으로 상태를 채웠으며, "
                "실제 등장과 행동은 화면·행동 설명을 따릅니다.")
        assumptions = story.get("assumptions")
        if isinstance(assumptions, list) and not any(
                isinstance(item, str) and item.startswith(NOTE_PREFIX) for item in assumptions):
            assumptions.append(note)
        return True
    except Exception:
        # Malformed output must reach the vendor validator and produce its
        # normal, bounded error instead of an adapter traceback.
        return False


def _validate(story, brief):
    if ACTIVE.get():
        complete_states(story, brief)
    return _vendor_validate_story(story, brief)


def install():
    if getattr(engine, "_storyboard_state_repair_installed", False):
        return
    engine.validate_story = _validate
    batch_generation.validate_story = _validate
    engine._storyboard_state_repair_installed = True