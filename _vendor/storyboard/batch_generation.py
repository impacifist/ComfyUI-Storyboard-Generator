"""Bounded outline-first generation; assemble only after every batch validates."""

import copy
import json

from . import providers
from .schema import NUMBER, STORY, TEXT, ValidationError, array, obj, validate, validate_story

SINGLE_CALL_LIMIT = 12
BATCH_SIZE = 6
PLAN = obj(summary=TEXT, beats=array(TEXT), assumptions=array(TEXT),
           shots=array(obj(id=TEXT, scene_id=TEXT, duration=NUMBER, purpose=TEXT, action=TEXT)))


def generate(brief, provider, model, director, previous=None, revision="", locked=None):
    locked = locked or {}
    previous_story = previous["story"] if previous else None
    compact_previous = None
    if previous_story:
        compact_previous = {"summary": previous_story["summary"], "beats": previous_story["beats"],
                            "shots": [{k: shot[k] for k in ("id", "scene_id", "duration", "purpose", "actions", "continuity")}
                                      for shot in previous_story["shots"]]}
    outline = providers.generate_json(provider, model, director + "\n" +
        "This call plans the ENTIRE storyboard, not detailed shots. Return only the supplied outline schema. "
        "Use exactly brief.shot_count entries in order, S01 onward. Allocate positive durations totaling "
        "brief.duration; preserve locked shot durations. Each action outlines causal setup, event and consequence. "
        "Resolve the requested ending only at the appropriate final beat. Plan the arc across all batches. "
        "Do not output dialogue, camera objects or character states in this planning call.",
        json.dumps({"task": "storyboard_outline", "brief": brief, "revision_request": revision,
                    "previous_story": compact_previous, "locked_shots": list(locked.values())}, ensure_ascii=False), PLAN)
    validate(outline, PLAN, "outline")
    expected = [f"S{i + 1:02d}" for i in range(brief["shot_count"])]
    if [s["id"] for s in outline["shots"]] != expected:
        raise ValidationError("전체 설계의 컷 수 또는 ID가 요청과 다릅니다. 기존 콘티는 유지됩니다.")
    for shot in outline["shots"]:
        if shot["id"] in locked:
            anchor = locked[shot["id"]]
            shot.update({k: anchor[k] for k in ("scene_id", "duration", "purpose")})
            shot["action"] = " / ".join(anchor["actions"])
        if not 0 < shot["duration"] <= 180 or any(not shot[k].strip() for k in ("scene_id", "purpose", "action")):
            raise ValidationError("전체 설계에 유효한 컷 길이와 행동이 필요합니다. 기존 콘티는 유지됩니다.")
    if abs(sum(s["duration"] for s in outline["shots"]) - brief["duration"]) > .1:
        raise ValidationError("전체 설계의 시간 합계가 목표 길이와 다릅니다. 기존 콘티는 유지됩니다.")
    if not outline["summary"].strip() or not outline["beats"]:
        raise ValidationError("전체 설계에 이야기 요약과 흐름이 필요합니다.")
    story = {k: copy.deepcopy(outline[k]) for k in ("summary", "beats", "assumptions")}
    story["shots"] = []
    cursor = 0
    while cursor < len(expected):
        if expected[cursor] in locked:
            story["shots"].append(copy.deepcopy(locked[expected[cursor]]))
            cursor += 1
            continue
        end = cursor
        while end < min(cursor + BATCH_SIZE, len(expected)) and expected[end] not in locked:
            end += 1
        ids = expected[cursor:end]
        following_anchor = next((locked[key] for key in expected[end:] if key in locked), None)
        try:
            batch = providers.generate_json(provider, model, director + "\n" +
                "This call expands ONLY batch.shot_ids from the approved full_outline. "
                "The brief describes the whole film, not content to finish in this batch. "
                "Return a STORY object with exactly those global shot IDs, in order; never restart IDs at S01. "
                "Use the assigned scene IDs and durations exactly. Preserve the full arc and do not rush the "
                "ending into an earlier batch. Continue previous_generated_shots: inherit character/prop "
                "states, active environment conditions, knowledge, emotional state, eyelines and camera axis. "
                "Use the next locked anchor when relevant to the handoff. Do not reset the scene at a batch boundary. "
                "A batch boundary is not a camera cut or a new scene. Do not output shots from other batches.",
                json.dumps({"task": "storyboard_batch", "brief": brief, "revision_request": revision,
                            "full_outline": outline, "batch": {"shot_ids": ids, "is_final": end == len(expected),
                            "planned_shots": outline["shots"][cursor:end]},
                            "previous_generated_shots": story["shots"][-2:], "next_locked_shot": following_anchor,
                            "previous_story": {"shots": previous_story["shots"][cursor:end]} if previous_story else None},
                           ensure_ascii=False), STORY)
            validate(batch, STORY, "batch")
            if [s["id"] for s in batch["shots"]] != ids:
                raise ValidationError("분할 생성 결과의 컷 수 또는 ID 순서가 다릅니다.")
            for shot, planned in zip(batch["shots"], outline["shots"][cursor:end]):
                if shot["duration"] != planned["duration"] or shot["scene_id"] != planned["scene_id"]:
                    raise ValidationError("분할 생성 결과가 전체 설계의 길이 또는 장면을 변경했습니다.")
                shot["locked"] = False
            # Validate each global-ID batch against the unchanged story contract.
            local = copy.deepcopy(batch)
            for index, shot in enumerate(local["shots"]):
                shot["id"] = f"S{index + 1:02d}"
            validate_story(local, {**brief, "shot_count": len(ids)})
        except (ValidationError, providers.ProviderError) as error:
            failure = providers.ProviderError if isinstance(error, providers.ProviderError) else ValidationError
            raise failure(f"{ids[0]}~{ids[-1]} 분할 생성 실패. 기존 콘티는 유지됩니다. 자동 재시도하지 않았습니다: {error}") from error
        story["shots"].extend(batch["shots"])
        story["assumptions"] = list(dict.fromkeys(story["assumptions"] + batch["assumptions"]))
        cursor = end
    validate_story(story, brief)
    return story
