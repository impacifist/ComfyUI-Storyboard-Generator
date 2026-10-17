"""Within-clip performance budgets and explicit, paired narrative handoffs."""

from .clip_planning import speech_seconds, update_estimates
from .schema import ValidationError


def annotate(document, layout):
    indices = {s["id"]: i for i, s in enumerate(document["story"]["shots"])}
    layout["handoffs"] = []
    for left, right in zip(layout["clips"], layout["clips"][1:]):
        outgoing, incoming = left["shots"][-1], right["shots"][0]
        distance = indices[incoming["id"]] - indices[outgoing["id"]]
        if distance not in (0, 1):
            continue  # An omitted source interval is not a continuous performance.
        same_shot = outgoing["id"] == incoming["id"]
        same_scene = outgoing["source"]["scene_id"] == incoming["source"]["scene_id"]
        kind = "continuous_shot" if same_shot else "planned_cut" if same_scene else "scene_change"
        layout["handoffs"].append({"id": f"H{len(layout['handoffs']) + 1:02d}",
            "from_clip": left["id"], "to_clip": right["id"], "kind": kind,
            "from_shot": outgoing["id"], "to_shot": incoming["id"],
            "boundary_id": outgoing.get("exit_boundary_id", ""),
            "outgoing_has_dialogue": bool(outgoing["source"]["dialogue"]),
            "incoming_has_dialogue": bool(incoming["source"]["dialogue"])})
    return layout


def refine(layout, draft):
    """Apply AI performance preferences only to the explicitly retimed auto mode.

    Original actions, speech ownership, source offsets, clip count and user-set
    clip lengths stay intact. Rough speech floors are advisory, not audio timing.
    """
    for clip in draft["clips"]:
        for shot in clip["shots"]:
            weight = shot["pacing_weight"]
            if not 0 <= weight <= 20:
                raise ValidationError("pacing_weight: use a number from 0 to 20")
    if layout["split_mode"] != "auto":
        return layout
    changed = 0
    for planned, directed in zip(layout["clips"], draft["clips"]):
        if planned["id"] != directed["id"] or [s["id"] for s in planned["shots"]] != [s["id"] for s in directed["shots"]]:
            raise ValidationError("변환 결과의 컷 수 또는 순서가 원본 계획과 다릅니다.")
        floors = [max(.25, speech_seconds(s["source"]["dialogue"]) + .35)
                  if s["source"]["dialogue"] else .25 for s in planned["shots"]]
        weights = [s["pacing_weight"] for s in directed["shots"]]
        remaining = planned["duration"] - sum(floors)
        # When the estimate cannot fit, never manufacture a faster delivery or
        # silently extend the clip. Keep the plan and its existing review notes.
        if remaining < 0 or not sum(weights) or len(floors) == 1:
            continue
        cursor = 0.0
        for index, shot in enumerate(planned["shots"]):
            duration = floors[index] + remaining * weights[index] / sum(weights)
            end = round(cursor + duration, 6) if index < len(floors) - 1 else planned["duration"]
            changed += abs(end - shot["end"]) > .001
            shot.update(start=round(cursor, 6), end=end)
            cursor = end
        planned["pacing_refined"] = True
    layout["pacing_refined"] = bool(changed)
    return update_estimates(layout)
