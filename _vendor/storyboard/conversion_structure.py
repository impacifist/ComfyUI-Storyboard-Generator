"""Source-owned clip/shot identities; never infer missing or renamed directions."""

from collections import Counter
import copy
import json

from .schema import ValidationError


RULES = (
    "Return every planned clip and every shot segment exactly once in its assigned clip, in plan order. "
    "Copy the exact clip IDs and source shot IDs from shot_contract. Never restart shot numbering at S01 "
    "in a new clip, renumber, merge, omit or move a shot to another clip. A source shot split across clips "
    "keeps the SAME source shot ID in each assigned clip; these are different continuation segments, "
    "not duplicates to remove. Bind each direction, camera, pacing weight and speech cue to that segment's "
    "source, source_offset and assigned dialogue. Video prompt display labels such as [Shot 1] are added "
    "by the application and are NOT JSON shot IDs. Return the complete object, never only changed clips."
)


def contract(layout):
    return {"rules": RULES, "clips": [{"id": c["id"], "shot_ids": [s["id"] for s in c["shots"]]}
                                      for c in layout["clips"]]}


def _ids(items):
    if not isinstance(items, list) or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) for x in items):
        return None  # Keep the more precise JSON-schema error for malformed fields.
    return [x["id"] for x in items]


def _display(ids):
    return json.dumps([x[:60] for x in ids[:100]], ensure_ascii=True)


def _difference(path, expected, actual, allow_reorder):
    if expected == actual or (allow_reorder and Counter(expected) == Counter(actual)):
        return None
    counts = Counter(actual)
    missing = [x for x in expected if x not in counts]
    extra = list(dict.fromkeys(x for x in actual if x not in expected))
    duplicates = [x for x, count in counts.items() if count > 1]
    details = [f"{path}: 예상 {len(expected)}개 {_display(expected)} / 응답 {len(actual)}개 {_display(actual)}"]
    for label, values in (("누락", missing), ("계획 외 ID", extra), ("중복", duplicates)):
        if values:
            details.append(f"{label} {_display(values)}")
    if not (missing or extra or duplicates):
        details.append("순서 불일치")
    return "; ".join(details)


def issues(layout, draft, *, allow_reorder=False):
    if not isinstance(draft, dict) or (actual := _ids(draft.get("clips"))) is None:
        return []
    expected = [c["id"] for c in layout["clips"]]
    found = []
    if problem := _difference("clips", expected, actual, allow_reorder):
        found.append(problem)
    # Pair by exact identity, never by positional zip or invented replacement IDs.
    by_id = {c["id"]: c for c in draft["clips"]}
    for planned in layout["clips"]:
        generated = by_id.get(planned["id"])
        if generated is None or (shot_ids := _ids(generated.get("shots"))) is None:
            continue
        if problem := _difference(f"clips.{planned['id']}.shots", [s["id"] for s in planned["shots"]],
                                  shot_ids, allow_reorder):
            found.append(problem)
    return found


def require_exact(layout, draft):
    if found := issues(layout, draft):
        raise ValidationError("클립·컷 구조 불일치: " + " | ".join(found))


def align(layout, draft):
    """Reorder only complete bijective ID matches, retaining whole objects intact."""
    if found := issues(layout, draft, allow_reorder=True):
        raise ValidationError("클립·컷 구조 불일치: " + " | ".join(found))
    result = copy.deepcopy(draft)
    changes = []
    if [c["id"] for c in result["clips"]] != [c["id"] for c in layout["clips"]]:
        changes.append("clips")
    clips = {c["id"]: c for c in result["clips"]}
    result["clips"] = [clips[c["id"]] for c in layout["clips"]]
    for planned, generated in zip(layout["clips"], result["clips"]):
        if [s["id"] for s in generated["shots"]] != [s["id"] for s in planned["shots"]]:
            changes.append(f"clips.{planned['id']}.shots")
            shots = {s["id"]: s for s in generated["shots"]}
            generated["shots"] = [shots[s["id"]] for s in planned["shots"]]
    require_exact(layout, result)
    return result, changes
