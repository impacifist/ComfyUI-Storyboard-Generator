"""Shared JSON contracts and deliberately bounded validation (no dependencies)."""

import math


class ValidationError(ValueError):
    pass


def obj(**properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


TEXT = {"type": "string"}
NUMBER = {"type": "number"}
CHARACTER = obj(id=TEXT, name=TEXT, personality=TEXT, speech=TEXT, desire=TEXT,
                fear=TEXT, habit=TEXT, fixed=TEXT)
CHARACTER["properties"].update(gender=TEXT, age=TEXT)
BRIEF = obj(title=TEXT, characters=array(CHARACTER), relationship=TEXT,
            location=TEXT, time=TEXT, atmosphere=TEXT, situation=TEXT,
            intent=TEXT, ending=TEXT, required=TEXT, excluded=TEXT, style=TEXT,
            duration=NUMBER, shot_count={"type": "integer"})
CHAR_STATE = obj(character_id=TEXT, position=TEXT, pose=TEXT, gaze=TEXT, emotion=TEXT)
PROP_STATE = obj(name=TEXT, holder=TEXT, position=TEXT)
STATE = obj(characters=array(CHAR_STATE), props=array(PROP_STATE))
SHOT = obj(id=TEXT, scene_id=TEXT, duration=NUMBER, purpose=TEXT, visual=TEXT,
           actions=array(TEXT), dialogue=array(obj(speaker=TEXT, text=TEXT, delivery=TEXT)),
           camera=obj(size=TEXT, angle=TEXT, movement=TEXT, transition=TEXT),
           start_state=STATE, end_state=STATE, continuity=TEXT,
           locked={"type": "boolean"})
STORY = obj(summary=TEXT, beats=array(TEXT), assumptions=array(TEXT), shots=array(SHOT))
FINDING = obj(severity={"type": "string", "enum": ["warning", "info"]},
              category=TEXT, shot_id=TEXT, message=TEXT)
AI_REVIEW = obj(summary=TEXT, findings=array(FINDING))


def validate(value, schema, path="root"):
    """Validate precisely the small schema subset used in this project."""
    kind = schema["type"]
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "boolean": isinstance(value, bool),
             "number": type(value) in (int, float), "integer": type(value) is int}[kind]
    if not valid:
        raise ValidationError(f"{path}: {kind} 형식이 필요합니다.")
    if kind in ("number", "integer") and not math.isfinite(value):
        raise ValidationError(f"{path}: 유한한 숫자여야 합니다.")
    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: 허용되지 않은 값입니다.")
    if kind == "string" and len(value) > 12000:
        raise ValidationError(f"{path}: 텍스트는 12,000자 이하여야 합니다.")
    if kind == "array":
        if len(value) > 100:
            raise ValidationError(f"{path}: 항목이 너무 많습니다.")
        for i, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{i}]")
    if kind == "object":
        if not set(schema["required"]) <= set(value) or not set(value) <= set(schema["properties"]):
            missing = set(schema["required"]) - set(value)
            extra = set(value) - set(schema["properties"])
            raise ValidationError(f"{path}: 필드 불일치 (누락: {', '.join(sorted(missing))}; "
                                  f"추가: {', '.join(sorted(extra))}).")
        for name, child in schema["properties"].items():
            if name in value:
                validate(value[name], child, f"{path}.{name}")


def validate_brief(brief):
    validate(brief, BRIEF, "brief")
    if not 1 <= len(brief["characters"]) <= 5:
        raise ValidationError("캐릭터는 1~5명까지 설정할 수 있습니다.")
    ids = [c["id"] for c in brief["characters"]]
    if len(set(ids)) != len(ids) or any(not i.strip() for i in ids):
        raise ValidationError("캐릭터 ID는 비어 있지 않고 서로 달라야 합니다.")
    for c in brief["characters"]:
        if not c["name"].strip() or not c["personality"].strip():
            raise ValidationError("캐릭터 이름과 성격을 입력해주세요.")
    labels = {"title": "프로젝트 이름", "location": "장소", "situation": "시작 상황",
              "intent": "원하는 상호작용", "ending": "원하는 결말"}
    for name, label in labels.items():
        if not brief[name].strip():
            raise ValidationError(f"{label} 항목을 입력해주세요.")
    if not 10 <= brief["duration"] <= 180 or not 3 <= brief["shot_count"] <= 60:
        raise ValidationError("목표 길이는 10~180초, 컷 수는 3~60개여야 합니다.")


def validate_story(story, brief):
    validate(story, STORY, "story")
    shots = story["shots"]
    if len(shots) != brief["shot_count"]:
        raise ValidationError(f"생성된 컷 수가 요청한 컷 수와 다릅니다. 요청 {brief['shot_count']}개 · 생성 {len(shots)}개")
    if not story["summary"].strip() or not story["beats"]:
        raise ValidationError("장면 요약과 감정 흐름이 필요합니다.")
    ids = {c["id"] for c in brief["characters"]}
    expected = [f"S{i + 1:02d}" for i in range(len(shots))]
    if [s["id"] for s in shots] != expected:
        raise ValidationError("컷 ID는 S01부터 순서대로 유일해야 합니다.")
    for shot in shots:
        if not 0 < shot["duration"] <= 180:
            raise ValidationError(f"{shot['id']}: 컷 길이는 0초 초과, 180초 이하여야 합니다.")
        for key in ("scene_id", "purpose", "visual", "continuity"):
            if not shot[key].strip():
                raise ValidationError(f"{shot['id']}.{key}: 필수 입력입니다.")
        if not shot["actions"] or any(not a.strip() for a in shot["actions"]):
            raise ValidationError(f"{shot['id']}: 구체적인 행동이 필요합니다.")
        if any(not value.strip() for value in shot["camera"].values()):
            raise ValidationError(f"{shot['id']}: 카메라 필드를 모두 입력해주세요.")
        for line in shot["dialogue"]:
            if line["speaker"] not in ids or not line["text"].strip():
                raise ValidationError(f"{shot['id']}: 화자 참조 또는 대사가 잘못되었습니다.")
        for key in ("start_state", "end_state"):
            states = shot[key]["characters"]
            if len(states) != len(ids) or {s["character_id"] for s in states} != ids:
                raise ValidationError(f"{shot['id']}.{key}: 모든 캐릭터의 상태가 필요합니다.")
            for state in states:
                if any(not v.strip() for v in state.values()):
                    raise ValidationError(f"{shot['id']}.{key}: 상태 설명이 비어 있습니다.")
            props = shot[key]["props"]
            if len({p["name"] for p in props}) != len(props):
                raise ValidationError(f"{shot['id']}: 소품 이름은 중복될 수 없습니다.")
            for prop in props:
                if not prop["name"].strip() or not prop["position"].strip():
                    raise ValidationError(f"{shot['id']}: 소품 이름과 위치가 필요합니다.")
                if prop["holder"] and prop["holder"] not in ids:
                    raise ValidationError(f"{shot['id']}: 소품 소유자 참조가 잘못되었습니다.")
