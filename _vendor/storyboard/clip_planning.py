"""Non-destructive dialogue allocation and explicit shared split boundaries."""

import copy
import math

from .schema import ValidationError


def speech_seconds(lines):
    # Same rough characters/second heuristic as local storyboard review; not measured audio.
    return round(sum(len("".join(line["text"].split())) for line in lines) / 5, 2)


def retimed(document, selected):
    result = copy.deepcopy(document)
    for shot in result["story"]["shots"]:
        if shot["id"] in selected and shot["dialogue"]:
            shot["duration"] = max(shot["duration"], math.ceil(speech_seconds(shot["dialogue"]) + .5))
    return result


def decorate(document, layout):
    originals = {shot["id"]: shot for shot in document["story"]["shots"]}
    entries = [(clip, shot) for clip in layout["clips"] for shot in clip["shots"]]
    layout["boundaries"] = []
    for index, (clip, shot) in enumerate(entries):
        if shot.get("continues_from_previous"):
            shot["source"].pop("start_state", None)
        if shot.get("continues_in_next"):
            shot["source"].pop("end_state", None)
            next_clip, next_shot = entries[index + 1]
            key = f"B{len(layout['boundaries']) + 1:02d}"
            shot["exit_boundary_id"] = key
            next_shot["entry_boundary_id"] = key
            original = originals[shot["id"]]
            layout["boundaries"].append({"id": key, "source_shot_id": shot["id"],
                "source_offset": shot["source_end"], "from_clip": clip["id"], "to_clip": next_clip["id"],
                "original_start_context": copy.deepcopy(original["start_state"]),
                "original_end_context": copy.deepcopy(original["end_state"])})

    if layout["split_mode"] in ("fixed", "auto"):
        for key, original in originals.items():
            segments = [s for _, s in entries if s["id"] == key]
            if not segments:
                continue
            remaining = [round(s["end"] - s["start"], 6) for s in segments]
            for segment in segments:
                segment["source"]["dialogue"] = []
                segment["dialogue_indices"] = []
            lines = copy.deepcopy(original["dialogue"])
            # Place each complete line at the earliest feasible part. Moving the
            # whole exchange to a later part can create an artificial silent tail.
            cursor = 0
            for line_index, line in enumerate(lines, 1):
                needed = speech_seconds([line])
                fitting = next((i for i in range(cursor, len(segments)) if remaining[i] >= needed), None)
                cursor = fitting if fitting is not None else max(range(cursor, len(segments)), key=remaining.__getitem__)
                segments[cursor]["source"]["dialogue"].append(line)
                segments[cursor]["dialogue_indices"].append(line_index)
                remaining[cursor] -= needed

    return update_estimates(layout)


def update_estimates(layout):
    layout["notes"] = []
    entries = [(clip, shot) for clip in layout["clips"] for shot in clip["shots"]]
    for clip, shot in entries:
        estimated = speech_seconds(shot["source"]["dialogue"])
        available = round(shot["end"] - shot["start"], 6)
        shot["speech_estimate_seconds"] = estimated
        if estimated > available:
            layout["notes"].append(f"{clip['id']} {shot['id']}: 대사 예상 {estimated:g}초 / 배정 {available:g}초. "
                                   "실제 음성 측정 전 추정치입니다. 대사 시간 확보 방식으로 다시 계획하거나 낭독 시간을 확인하세요.")
    return layout


def automatic(document, selected, limit):
    """Prefer intact shots; optimize all boundaries instead of filling each window."""
    atoms = []
    source_cursor = 0
    for index, original in enumerate(document["story"]["shots"]):
        source_start = source_cursor
        source_cursor += original["duration"]
        if original["id"] not in selected:
            continue
        speech = speech_seconds(original["dialogue"])
        duration = max(original["duration"], math.ceil(speech + .5) if speech else 0)
        parts = math.ceil(duration / limit)
        # A long continuous shot is split near an utterance boundary when feasible.
        safe, cursor = [0.0], .25
        for line in original["dialogue"]:
            safe.append(cursor)
            cursor += speech_seconds([line])
            safe.append(cursor)
            cursor += .25
        elapsed = 0.0
        for part in range(parts):
            if part == parts - 1:
                end = duration
            else:
                lower = max(elapsed + .001, duration - (parts - part - 1) * limit)
                upper = min(elapsed + limit, duration - .001)
                target = elapsed + (duration - elapsed) / (parts - part)
                candidates = [value for value in safe if lower <= value <= upper]
                end = min(candidates, key=lambda value: abs(value - target)) if candidates else target
            offset = round(original["duration"] * elapsed / duration, 6)
            source_end = round(original["duration"] * end / duration, 6)
            atoms.append({"id": original["id"], "scene_id": original["scene_id"], "index": index,
                          "duration": round(end - elapsed, 6), "source": copy.deepcopy(original),
                          "source_offset": offset, "source_end": source_end,
                          "source_duration": original["duration"],
                          "continues_from_previous": part > 0, "continues_in_next": part < parts - 1,
                          "source_timeline_start": round(source_start + offset, 6),
                          "source_timeline_end": round(source_start + source_end, 6)})
            elapsed = end
    # Minimize padding and extra clips, then prefer balanced lengths. Never combine
    # different scenes or cross a gap in the selected source shots.
    costs, previous = [0.0] + [math.inf] * len(atoms), [-1] * (len(atoms) + 1)
    for end in range(1, len(atoms) + 1):
        duration = 0.0
        for start in range(end - 1, -1, -1):
            atom = atoms[start]
            if start < end - 1 and (atom["scene_id"] != atoms[start + 1]["scene_id"]
                                   or atoms[start + 1]["index"] - atom["index"] > 1):
                break
            duration = round(duration + atom["duration"], 6)
            if duration > limit + .000001:
                break
            padding = max(0, min(4, limit) - duration)
            cost = costs[start] + 2 + padding * 5 + ((limit - duration) / limit) ** 2
            if cost < costs[end]:
                costs[end], previous[end] = cost, start
    groups, cursor = [], len(atoms)
    while cursor:
        groups.append((previous[cursor], cursor))
        cursor = previous[cursor]
    clips = []
    for start, end in reversed(groups):
        clip = {"id": f"C{len(clips) + 1:02d}", "scene_id": atoms[start]["scene_id"],
                "shots": [], "duration": 0,
                "timeline_start": atoms[start]["source_timeline_start"],
                "timeline_end": atoms[end - 1]["source_timeline_end"],
                "break_reason": "continuation" if atoms[end - 1]["continues_in_next"] else "shot_end"}
        for atom in atoms[start:end]:
            shot = {k: v for k, v in atom.items() if k not in
                    ("scene_id", "index", "duration", "source_timeline_start", "source_timeline_end")}
            shot.update(start=clip["duration"], end=round(clip["duration"] + atom["duration"], 6))
            if clip["shots"] and clip["shots"][-1]["id"] == shot["id"]:
                clip["shots"][-1].update(end=shot["end"], source_end=shot["source_end"],
                                         continues_in_next=shot["continues_in_next"])
            else:
                clip["shots"].append(shot)
            clip["duration"] = shot["end"]
        clip["recommended_duration"] = clip["duration"]
        clips.append(clip)
    return decorate(document, {"max_seconds": limit, "split_mode": "auto", "clips": clips,
                    "original_selected_duration": sum(s["duration"] for s in document["story"]["shots"]
                                                      if s["id"] in selected)})


def set_lengths(document, layout, overrides, minimum, whole_seconds):
    """Explicit conversion-only retiming, never mutate the saved storyboard."""
    if not isinstance(overrides, dict) or any(key not in {c["id"] for c in layout["clips"]} for key in overrides):
        raise ValidationError("클립 길이 설정이 현재 분할 계획과 다릅니다. 자동 추천을 다시 실행해주세요.")
    for clip in layout["clips"]:
        old = clip["duration"]
        recommended = max(minimum, math.ceil(old - .0000001)) if whole_seconds else max(minimum, old)
        clip["recommended_duration"] = recommended
        chosen = overrides.get(clip["id"], recommended)
        if (type(chosen) not in (int, float) or not minimum <= chosen <= layout["max_seconds"]
                or (whole_seconds and chosen != int(chosen))):
            raise ValidationError("클립 길이는 허용 범위 안의 숫자로 입력해주세요. 공식 가이드는 정수 초만 지원합니다.")
        clip["duration"] = int(chosen) if whole_seconds else chosen
        clip["timing_adjusted"] = chosen != old
        for shot in clip["shots"]:
            shot["start"] = round(shot["start"] * chosen / old, 6)
            shot["end"] = round(shot["end"] * chosen / old, 6)
        clip["shots"][-1]["end"] = clip["duration"]
        clip["manually_adjusted"] = clip["id"] in overrides and chosen != recommended
    layout["timing_adjusted"] = True
    return decorate(document, layout)
