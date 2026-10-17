"""Assemble model syntax, shot order, timing and verbatim speech outside the LLM."""

import json
import re
import unicodedata

from .schema import CHAR_STATE, NUMBER, TEXT, ValidationError, array, obj, validate

DIRECTION_STATE = obj(characters=array(CHAR_STATE),
                      props=array(obj(name=TEXT, english_name=TEXT, holder=TEXT, position=TEXT)))

DIRECTOR_OUTPUT = obj(clips=array(obj(
    id=TEXT, context=TEXT, subject_definitions=TEXT, summary=TEXT, retention_analysis=TEXT,
    shots=array(obj(id=TEXT, direction=TEXT, pacing_weight=NUMBER, speech_cues=array(TEXT),
                    camera=obj(size=TEXT, angle=TEXT, movement=TEXT, transition=TEXT, layout=TEXT),
                    dialogue_language=TEXT, deliveries=array(TEXT))),
    overall_soundscape=TEXT, non_diegetic_music=TEXT)), boundaries=array(obj(id=TEXT, state=DIRECTION_STATE)),
    handoffs=array(obj(id=TEXT, bridge=TEXT, sound_bridge=TEXT)),
    reference_notes=array(obj(label=TEXT, note=TEXT)),
    warnings=array(TEXT), notes=array(TEXT))


def require_english(value, path):
    # No dependency or probabilistic language guess: reject non-English scripts and
    # combining accents. Punctuation such as curly quotes and dashes remains valid.
    if any(unicodedata.category(c)[0] in "LM" and not ("A" <= c <= "Z" or "a" <= c <= "z") for c in value):
        raise ValidationError(f"{path}: English-only instructions required; translate this field into English")


def render_labels(document):
    labels = {}
    for index, character in enumerate(document["brief"]["characters"], 1):
        fallback = f"Character {index}"
        name, key = character["name"], character["id"]
        try:
            require_english(name + key, "identity")
            # Identifiers must be plain tokens, never rendering syntax.
            if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
                raise ValidationError("identity")
            if not re.fullmatch(r"[A-Za-z0-9 _.'-]+", name):
                raise ValidationError("identity")
            labels[key] = f"{name} [{key}]"
        except ValidationError:
            labels[key] = fallback
    return labels


def output_schema(document, layout):
    """Bind reference fields to this storyboard instead of unconstrained TEXT."""
    # TEXT is deliberately shared in base contracts. Break aliases before adding enums.
    schema = json.loads(json.dumps(DIRECTOR_OUTPUT))
    boundary = schema["properties"]["boundaries"]["items"]["properties"]
    ids = [c["id"] for c in document["brief"]["characters"]]
    boundary["id"]["enum"] = [b["id"] for b in layout.get("boundaries", [])] or ["unused"]
    schema["properties"]["handoffs"]["items"]["properties"]["id"]["enum"] = [h["id"] for h in layout.get("handoffs", [])] or ["unused"]
    state = boundary["state"]["properties"]
    character = state["characters"]["items"]["properties"]
    character["character_id"]["enum"] = ids
    state["props"]["items"]["properties"]["holder"]["enum"] = ["", *ids]
    return schema


def boundary_issues(document, layout, draft):
    """Precise structural/semantic feedback, without echoing model prose."""
    ids = [c["id"] for c in document["brief"]["characters"]]
    expected = [b["id"] for b in layout.get("boundaries", [])]
    if [b["id"] for b in draft["boundaries"]] != expected:
        return ["boundaries: 예상 ID/순서 " + (", ".join(expected) or "[]")]
    issues = []
    for boundary, planned in zip(draft["boundaries"], layout.get("boundaries", [])):
        prefix = f"boundaries.{boundary['id']}.state"
        state = boundary["state"]
        actual = [c["character_id"] for c in state["characters"]]
        if len(actual) != len(ids) or set(actual) != set(ids):
            issues.append(f"{prefix}.characters: 모든 캐릭터 ID가 중복 없이 한 번씩 필요합니다 ({', '.join(ids)})")
        for index, character in enumerate(state["characters"]):
            for field, value in character.items():
                if not value.strip():
                    issues.append(f"{prefix}.characters[{index}].{field}: 빈 값입니다")
        for index, prop in enumerate(state["props"]):
            for field in ("name", "position"):
                if not prop[field].strip():
                    issues.append(f"{prefix}.props[{index}].{field}: 빈 값입니다")
            if prop["holder"] and prop["holder"] not in ids:
                issues.append(f"{prefix}.props[{index}].holder: 캐릭터 ID 또는 빈 문자열만 허용됩니다")
        if len({p["name"] for p in state["props"]}) != len(state["props"]):
            issues.append(f"{prefix}.props.name: 소품 이름이 중복되었습니다")
        # A prop present at BOTH source endpoints cannot disappear at the split.
        start_props = {p["name"] for p in planned["original_start_context"]["props"]}
        end_props = {p["name"] for p in planned["original_end_context"]["props"]}
        if not (start_props & end_props) <= {p["name"] for p in state["props"]}:
            issues.append(f"{prefix}.props: 원본 시작·종료에 공통으로 존재하는 소품이 누락되었습니다")
    return issues


def language(text, suggested):
    # Script signals take precedence over AI labels; Latin-language distinctions use its metadata.
    for pattern, name in ((r"[가-힣]", "Korean"), (r"[ぁ-ヿ]", "Japanese"), (r"[一-鿿]", "Chinese")):
        if re.search(pattern, text):
            return name
    allowed = {"Arabic", "Chinese", "English", "French", "German", "Italian", "Japanese",
               "Korean", "Portuguese", "Russian", "Spanish"}
    return suggested if suggested in allowed else "English"


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    return f"{milliseconds // 60000:02d}:{milliseconds // 1000 % 60:02d}.{milliseconds % 1000:03d}"


def export_text(result):
    if result.get("output_language") != "english_except_dialogue":
        raise ValidationError("영어 전용 규칙 적용 전 결과입니다. 콘티를 다시 변환해주세요.")
    model = result["target_model"]
    if not all(" " <= c <= "~" for c in model):
        model = "Custom video model"
    lines = ["VIDEO PROMPTS", "=" * 60, model, ""]
    if result["output"].get("english_notes"):
        lines.extend(["REVIEW NOTES", *result["output"]["english_notes"], ""])
    if result.get("references"):
        lines.append("REFERENCE ATTACHMENT ORDER")
        notes = {r["label"]: r["note"] for r in result["english_reference_notes"]}
        for item in result["references"]:
            note = notes[item["label"]]
            owner = "Background" if item["role"] == "environment" else result["render_labels"][item["character_id"]]
            lines.append(f"{item['order']}. {item['label']} | {owner} | {item['role']}"
                         + (f" | {note}" if note else ""))
        lines.append("")
    plans = {c["id"]: c for c in result["plan"]["clips"]}
    for clip in result["output"]["clips"]:
        planned = plans[clip["id"]]
        lines.extend(["-" * 60, f"{clip['id']} | {planned['duration']:g}s"])
        if "timeline_start" in planned:
            lines.append(f"Source {planned['timeline_start']:g}–{planned['timeline_end']:g}s")
        lines.extend(["-" * 60, "", clip["prompt"].strip(), ""])
    return "\r\n".join(lines)


def h3_reference_labels(draft, assets):
    """Canonicalize attachment aliases in AI prose, never original dialogue or IDs."""
    allowed = {item["label"] for item in assets}
    aliases = re.compile(r"<(?:Image|Picture)\s*(\d+)>|\b(?:Image|Picture)\s+(\d+)\b", re.IGNORECASE)

    def replace(match):
        label = f"<Picture {int(match[1] or match[2])}>"
        if label not in allowed:
            raise ValidationError("프롬프트의 이미지 번호와 첨부 목록이 일치하지 않습니다.")
        return label

    def normalize(value, key=""):
        if isinstance(value, dict):
            return {field: normalize(item, field) for field, item in value.items()}
        if isinstance(value, list):
            return [normalize(item, key) for item in value]
        if isinstance(value, str) and key not in {"id", "character_id", "holder", "name"}:
            return aliases.sub(replace, value)
        return value

    return normalize(draft)


def assemble(document, layout, draft, profile, assets):
    validate(draft, DIRECTOR_OUTPUT, "director_output")
    if profile and profile["id"].startswith("minimax"):
        draft = h3_reference_labels(draft, assets)
    if [c["id"] for c in draft["clips"]] != [c["id"] for c in layout["clips"]]:
        raise ValidationError("변환 결과의 클립 수 또는 순서가 원본 계획과 다릅니다.")
    names = render_labels(document)
    if [h["id"] for h in draft["handoffs"]] != [h["id"] for h in layout.get("handoffs", [])]:
        raise ValidationError("handoffs: return every planned handoff once, in plan order")
    for handoff in draft["handoffs"]:
        for field in ("bridge", "sound_bridge"):
            require_english(handoff[field], f"handoffs.{handoff['id']}.{field}")
            if not handoff[field].strip() or re.search(r"</?d>|\(S\d+\)|\{[^{}]*\}", handoff[field]):
                raise ValidationError("handoffs: nonempty English connection notes without dialogue syntax required")
    bridges = {h["id"]: h for h in draft["handoffs"]}
    if [r["label"] for r in draft["reference_notes"]] != [a["label"] for a in assets]:
        raise ValidationError("reference_notes: return every reference label once, in manifest order")
    for index, reference in enumerate(draft["reference_notes"]):
        require_english(reference["note"], f"reference_notes[{index}].note")
        if re.search(r"</?d>|\(S\d+\)|\{[^{}]*\}", reference["note"]):
            raise ValidationError("reference_notes.note: dialogue syntax is forbidden")
    for index, note in enumerate(draft["notes"]):
        require_english(note, f"notes[{index}]")
    issues = boundary_issues(document, layout, draft)
    if issues:
        raise ValidationError("공유 경계 상태 검증 실패: " + "; ".join(issues))
    boundaries = {}
    for boundary in draft["boundaries"]:
        state = boundary["state"]
        for index, character in enumerate(state["characters"]):
            for field in ("position", "pose", "gaze", "emotion"):
                require_english(character[field], f"boundaries.{boundary['id']}.characters[{index}].{field}")
        for index, prop in enumerate(state["props"]):
            for field in ("english_name", "position"):
                require_english(prop[field], f"boundaries.{boundary['id']}.props[{index}].{field}")
            if not prop["english_name"].strip():
                raise ValidationError("boundary.props.english_name: English prop name required")
        if any(re.search(r"</?d>|\(S\d+\)|\{[^{}]*\}", value)
               for item in state["characters"] + state["props"] for value in item.values()):
            raise ValidationError("AI 연출에 대사 문법이 포함되었습니다. 대사는 프로그램이 삽입해야 합니다.")
        descriptions = [f"{names[c['character_id']]}: position={c['position']}; "
                        f"pose={c['pose']}; gaze={c['gaze']}; emotion={c['emotion']}" for c in state["characters"]]
        descriptions += [f"Prop {p['english_name']}: holder={names.get(p['holder'], 'unheld')}; position={p['position']}" for p in state["props"]]
        boundaries[boundary["id"]] = " | ".join(descriptions)
    h3 = bool(profile and profile["id"].startswith("minimax"))
    seedance = bool(profile and profile["id"].startswith("seedance"))
    # A time split is not a second camera design. Bind each source shot once;
    # composition notes may evolve with the segment's continuing performance.
    cameras = {}
    for clip in draft["clips"]:
        for shot in clip["shots"]:
            cameras.setdefault(shot["id"], shot["camera"])
    rendered, manifest = [], []
    for generated, clip in zip(draft["clips"], layout["clips"]):
        if [s["id"] for s in generated["shots"]] != [s["id"] for s in clip["shots"]]:
            raise ValidationError("변환 결과의 컷 수 또는 순서가 원본 계획과 다릅니다.")
        if not generated["context"].strip() or any(not s["direction"].strip() for s in generated["shots"]):
            raise ValidationError("빈 프롬프트가 반환되었습니다.")
        fragments = [generated[key] for key in ("context", "subject_definitions", "summary", "retention_analysis",
                                                "overall_soundscape", "non_diegetic_music")]
        fragments += [s["direction"] for s in generated["shots"]]
        fragments += [value for s in generated["shots"] for value in s["camera"].values()]
        fragments += [value for h in draft["handoffs"] for value in (h["bridge"], h["sound_bridge"])]
        for field in ("context", "subject_definitions", "summary", "retention_analysis", "overall_soundscape", "non_diegetic_music"):
            require_english(generated[field], f"clips.{clip['id']}.{field}")
        for index, directed in enumerate(generated["shots"]):
            for field, value in directed["camera"].items():
                require_english(value, f"clips.{clip['id']}.shots[{index}].camera.{field}")
                if not value.strip():
                    raise ValidationError(f"clips.{clip['id']}.shots[{index}].camera.{field}: explicit camera instruction required")
            require_english(directed["direction"], f"clips.{clip['id']}.shots[{index}].direction")
            require_english(directed["dialogue_language"], f"clips.{clip['id']}.shots[{index}].dialogue_language")
            fragments.extend(directed["deliveries"] + directed["speech_cues"])
            for line_index, delivery in enumerate(directed["deliveries"]):
                require_english(delivery, f"clips.{clip['id']}.shots[{index}].deliveries[{line_index}]")
            for line_index, cue in enumerate(directed["speech_cues"]):
                require_english(cue, f"clips.{clip['id']}.shots[{index}].speech_cues[{line_index}]")
                if not cue.strip():
                    raise ValidationError("speech_cues: one concrete English onset cue per assigned dialogue line required")
        # Explicit dialogue syntax is owned by this renderer, never the model.
        if any(re.search(r"</?d>|\(S\d+\)|\{[^{}]*\}", text) for text in fragments):
            raise ValidationError("AI 연출에 대사 문법이 포함되었습니다. 대사는 프로그램이 삽입해야 합니다.")
        if profile:
            allowed = {a["label"] for a in assets}
            used = [label for text in fragments for label in re.findall(r"<Picture \d+>|\bImage \d+\b", text)]
            if any(label not in allowed for label in used):
                raise ValidationError("프롬프트의 이미지 번호와 첨부 목록이 일치하지 않습니다.")
        bodies, speakers = [generated["context"]], {}
        incoming = next((h for h in layout.get("handoffs", []) if h["to_clip"] == clip["id"]), None)
        outgoing = next((h for h in layout.get("handoffs", []) if h["from_clip"] == clip["id"]), None)
        if incoming:
            bridge = bridges[incoming["id"]]
            bodies.append(f"Incoming connection {incoming['id']} ({incoming['kind']}): {bridge['bridge']}\n"
                          f"Audio connection: {bridge['sound_bridge']}")
            if incoming["kind"] != "scene_change":
                bodies.append("The scene is already underway. Continue its conversational rhythm; do not restart "
                              "the setup or force speech to begin simply because this clip starts. "
                              "Let each assigned line follow its stated action or response cue.")
        for index, (directed, planned) in enumerate(zip(generated["shots"], clip["shots"]), 1):
            if (len(directed["deliveries"]) != len(planned["source"]["dialogue"])
                    or len(directed["speech_cues"]) != len(planned["source"]["dialogue"])):
                raise ValidationError(f"clips.{clip['id']}.shots[{index - 1}].deliveries: one English translation per assigned dialogue line required")
            if h3:
                heading = f"[Shot {index}]" + (f" At {timestamp(planned['start'])}," if index > 1 else "")
            else:
                heading = f"[Shot {index}] {planned['start']:g}–{planned['end']:g}s"
            body = [heading]
            if layout.get("timing_adjusted"):
                body.append("Timing: let the approved action, speech and reaction unfold as one natural beat. "
                            "The shot heading locates the planned edit; do not turn the performance into "
                            "a second-by-second checklist or wait for a clip boundary to speak. "
                            "Preserve intentional silence and held compositions; add no filler pause or repeated action.")
            camera = cameras[planned["id"]]
            body.append(f"Camera: {camera['size']}; angle: {camera['angle']}; movement: {camera['movement']}.")
            body.append("Layout: " + directed["camera"]["layout"])
            if planned.get("continues_from_previous"):
                body.append("Continue the same source shot and ongoing camera motion; do not replay its opening or add a cut.")
            if planned.get("entry_boundary_id"):
                key = planned["entry_boundary_id"]
                body.append(f"Start at shared boundary {key}: {boundaries[key]}")
            body.append(directed["direction"])
            for line_index, line in enumerate(planned["source"]["dialogue"], 1):
                if not line["text"]:
                    continue
                speaker = line["speaker"]
                if speaker not in speakers:
                    speakers[speaker] = len(speakers) + 1
                spoken_language = language(line["text"], directed["dialogue_language"])
                attribution = names[speaker]
                translated_delivery = directed["deliveries"][line_index - 1]
                if line["delivery"] and not translated_delivery.strip():
                    raise ValidationError(f"clips.{clip['id']}.{planned['id']}.deliveries: missing delivery translation")
                if not line["delivery"] and translated_delivery:
                    raise ValidationError(f"clips.{clip['id']}.{planned['id']}.deliveries: do not invent delivery instructions")
                delivery = f" Delivery: {translated_delivery}." if translated_delivery else ""
                body.append("Speech onset: " + directed["speech_cues"][line_index - 1])
                if h3:
                    speech = f"(S{speakers[speaker]}) {attribution}.{delivery} <d>[{spoken_language}] {line['text']}</d>"
                elif seedance:
                    speech = f"{attribution} says in {spoken_language}.{delivery} {{{line['text']}}}"
                else:
                    speech = f"{attribution} says in {spoken_language}.{delivery} {line['text']}"
                body.append(speech)
                original_index = planned.get("dialogue_indices", list(range(1, len(planned["source"]["dialogue"]) + 1)))[line_index - 1]
                manifest.append({"clip_id": clip["id"], "shot_id": planned["id"], "line": original_index,
                                 "speaker": speaker, "language": spoken_language, "text": line["text"]})
            if planned.get("exit_boundary_id"):
                key = planned["exit_boundary_id"]
                body.append(f"End at shared boundary {key}: {boundaries[key]}")
            has_hold = index == len(clip["shots"]) and "content_duration" in clip
            if has_hold:
                body.append(f"From {clip['content_duration']:g}s to {clip['duration']:g}s, hold the final frame. "
                            "Add no dialogue, action, camera motion or new shot. Apply the ending transition only after this hold.")
            if planned.get("continues_in_next"):
                body.append("Continue this source shot into the next clip without an edit or camera reset.")
            else:
                ending = "After the final-frame hold: " if has_hold else "At the end of this source shot: "
                body.append(ending + camera["transition"])
            bodies.append("\n".join(body))
        if outgoing:
            bridge = bridges[outgoing["id"]]
            bodies.append(f"Outgoing connection {outgoing['id']} ({outgoing['kind']}): {bridge['bridge']}\n"
                          f"Audio connection: {bridge['sound_bridge']}")
            if outgoing["kind"] != "scene_change":
                bodies.append("This is an intermediate generation segment, not a scene ending. "
                              "Carry the approved performance into the next segment without an added fade, "
                              "settling pose or silent countdown. Keep intentional pauses only where the story calls for them.")
        description = "\n\n".join(bodies)
        refs = []
        for item, translated in zip(assets, draft["reference_notes"]):
            if item["note"] and not translated["note"].strip():
                raise ValidationError("reference_notes.note: missing English reference translation")
            if item["role"] == "environment":
                refs.append(f"Background — {item['label']}; environment reference. {translated['note']} "
                            "Use this reference for the matching location's architecture and spatial layout. "
                            "Preserve the relative positions of seats, doors, windows, aisles and fixed landmarks "
                            "across shots and clips, including reverse angles. Change viewpoint, not the set geometry. "
                            "Do not copy people from the background image or use it as a character identity reference. "
                            "Keep approved character actions and camera direction; apply this reference only to its matching location.")
                continue
            character_index = next(i for i, c in enumerate(document["brief"]["characters"], 1)
                                   if c["id"] == item["character_id"])
            identity = f"<Subject {character_index}> " if h3 else ""
            refs.append(f"{identity}{names[item['character_id']]} — {item['label']}; "
                        f"reference role: {item['role']}. {translated['note']}")
        if h3:
            values = {"subject_definitions": "\n".join(refs + [generated["subject_definitions"]]),
                      "summary": generated["summary"], "retention_analysis": generated["retention_analysis"],
                      "detailed_description": description, "integrated_multimodal_description": description,
                      "overall_soundscape": generated["overall_soundscape"] or "N/A",
                      "non_diegetic_music": generated["non_diegetic_music"] or "N/A"}
            prompt = "\n\n".join(f"{heading}\n{values[heading]}" for heading in profile["sections"])
        else:
            prompt = "\n\n".join([*refs, description,
                "Overall soundscape: " + (generated["overall_soundscape"] or "N/A"),
                "Non-diegetic music: " + (generated["non_diegetic_music"] or "N/A")])
        rendered.append({"id": clip["id"], "prompt": prompt})
    english_notes = list(draft["notes"])
    if layout.get("pacing_refined"):
        english_notes.append("Within-clip shot allocations were refined around dialogue and performance cues. "
                             "Clip lengths, source shot order and original dialogue are unchanged; review actual voice timing.")
    if layout.get("timing_adjusted"):
        english_notes.append(f"Conversion-only timing: source selection {layout['original_selected_duration']:g}s; "
                             f"planned playback {sum(c['duration'] for c in layout['clips']):g}s. "
                             "Original storyboard and dialogue are unchanged. Recommended speech timing is an estimate, not measured audio.")
    for clip in layout["clips"]:
        if "content_duration" in clip:
            english_notes.append(f"{clip['id']}: source content {clip['content_duration']:g}s; generated duration "
                                 f"{clip['duration']:g}s. Hold the final frame for the remaining time; source timing is unchanged.")
        for shot in clip["shots"]:
            available = shot["end"] - shot["start"]
            if shot.get("speech_estimate_seconds", 0) > available:
                english_notes.append(f"{clip['id']} {shot['id']}: estimated speech {shot['speech_estimate_seconds']:g}s / allotted {available:g}s. Estimate only; review actual voice timing.")
    return {"clips": rendered, "warnings": draft["warnings"], "english_notes": english_notes,
            "notes": list(dict.fromkeys(layout.get("notes", []) + draft["notes"]))}, manifest
