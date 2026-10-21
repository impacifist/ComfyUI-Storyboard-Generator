"""Local immutable image assets and editable per-storyboard selections."""

import base64
import binascii
import hashlib
import io
import json
import re
import uuid
import zipfile

from . import library
from .schema import ValidationError

ROLES = ("appearance", "face", "body", "outfit", "expression", "detail")
KINDS = ("character", "background", "prop", "other")
ROLE_GUIDANCE = {
    "appearance": "Use this image for this character's face, hairstyle, clothing, colors and accessories.",
    "face": "Use this image for the face and hairstyle; keep clothing and actions from the approved storyboard or outfit reference.",
    "body": "Use this image for body proportions and silhouette; preserve the approved action and camera framing.",
    "outfit": "Use this image for clothing and accessories, without changing the character's facial identity.",
    "expression": "Use this image for the intended facial expression, without replacing the character's identity or clothing.",
    "detail": "Use only the specific visual details identified in the reference note.",
    "environment": "Use this image for the location's architecture and spatial layout, not for character identity.",
    "prop": "Preserve this prop's appearance whenever it occurs in the approved action. Track its actual holder and location through the source states; do not invent possession, a transfer or an extra object.",
    "other": "Apply only the explicitly described visual reference purpose. Do not copy unrelated people, objects or actions from this image.",
}
BACKGROUND_ROLE = "environment"
MAX_IMAGE = 5_000_000


def tables(db):
    db.execute("CREATE TABLE IF NOT EXISTS reference_assets "
               "(id TEXT PRIMARY KEY, board_id TEXT, character_id TEXT, name TEXT, mime TEXT, sha256 TEXT, data BLOB)")
    db.execute("CREATE TABLE IF NOT EXISTS reference_selections (board_id TEXT PRIMARY KEY, selection TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS reference_targets "
               "(asset_id TEXT PRIMARY KEY, kind TEXT, target_id TEXT, target_name TEXT, owner_id TEXT)")


def metadata(row):
    """Legacy images retain their immutable character/background assignment."""
    with library.database() as db:
        tables(db)
        target = db.execute("SELECT * FROM reference_targets WHERE asset_id=?", (row["id"],)).fetchone()
    if target:
        return {key: target[key] for key in ("kind", "target_id", "target_name", "owner_id")}
    return {"kind": "character" if row["character_id"] else "background",
            "target_id": "character:" + row["character_id"] if row["character_id"] else "legacy-background",
            "target_name": "", "owner_id": ""}


def kind(item):
    return item.get("kind", "background" if item["role"] == BACKGROUND_ROLE else "character")


def target_key(item):
    return item.get("target_id", "character:" + item["character_id"] if item["character_id"] else "legacy-background")


def applies(item, shot_id):
    return not item.get("shot_ids") or shot_id in item["shot_ids"]


def target_bindings(assets, character_count):
    groups, counts = {}, {"prop": 0, "other": 0, "background": 0}
    for item in assets:
        item_kind = kind(item)
        if item_kind == "character":
            continue
        key = target_key(item)
        if key not in groups:
            counts[item_kind] += 1
            groups[key] = {"target_id": key, "kind": item_kind, "name": item.get("target_name", ""),
                           "label": {"prop": "Prop", "other": "Visual reference", "background": "Background"}[item_kind] + f" {counts[item_kind]}",
                           "subject": f"<Subject {character_count + counts['prop']}>" if item_kind == "prop" else "",
                           "owner_id": item.get("owner_id", ""), "pictures": [], "shot_ids": item.get("shot_ids", [])}
        groups[key]["pictures"].append(item["label"])
    return list(groups.values())


def validate_scope(shot_ids, board):
    allowed = {s["id"] for s in board["story"]["shots"]}
    if (not isinstance(shot_ids, list) or any(not isinstance(s, str) or s not in allowed for s in shot_ids)
            or len(set(shot_ids)) != len(shot_ids)):
        raise ValidationError("레퍼런스를 적용할 컷을 확인해주세요.")


def upload(payload):
    board = library.load(payload.get("id"))
    item_kind = payload.get("kind", "character")
    background = item_kind == "background"
    if item_kind not in KINDS:
        raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
    character = payload.get("character_id") if item_kind == "character" else ""
    if item_kind != "character" and payload.get("character_id") not in (None, ""):
        raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
    character_ids = [c["id"] for c in board["brief"]["characters"]]
    if item_kind == "character" and character not in character_ids:
        raise ValidationError("참조 이미지의 캐릭터가 원본 콘티와 다릅니다.")
    target_name, owner = payload.get("target_name", ""), payload.get("owner_id", "")
    note, shot_ids = payload.get("note", ""), payload.get("shot_ids", [])
    if (not isinstance(target_name, str) or len(target_name) > 100 or not isinstance(owner, str)
            or (owner and (item_kind != "prop" or owner not in character_ids))):
        raise ValidationError("참조 대상의 이름과 소유자를 확인해주세요.")
    if item_kind in ("prop", "other") and not target_name.strip():
        raise ValidationError("소품 또는 그 외 참조 대상의 이름을 입력해주세요.")
    if not isinstance(note, str) or len(note) > 1000 or (item_kind == "other" and not note.strip()):
        raise ValidationError("그 외 레퍼런스는 참고할 내용을 입력해주세요.")
    validate_scope(shot_ids, board)
    target_id = "character:" + character if item_kind == "character" else payload.get("target_id") or uuid.uuid4().hex
    if not isinstance(target_id, str) or len(target_id) > 150:
        raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
    if payload.get("target_id") and item_kind != "character":
        with library.database() as db:
            tables(db)
            rows = db.execute("SELECT id, character_id FROM reference_assets WHERE board_id=?", (payload["id"],)).fetchall()
        match = next((m for row in rows if (m := metadata(row))["target_id"] == target_id), None)
        if match is None or any(match[k] != v for k, v in (("kind", item_kind), ("target_name", target_name), ("owner_id", owner))):
            raise ValidationError("참조 대상이 원본 저장 항목과 다릅니다.")
    value = payload.get("data")
    if not isinstance(value, str):
        raise ValidationError("PNG, JPEG, WebP 이미지를 선택해주세요.")
    match = re.fullmatch(r"data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)", value)
    if not match:
        raise ValidationError("PNG, JPEG, WebP 이미지를 선택해주세요.")
    try:
        data = base64.b64decode(match[2], validate=True)
    except (ValueError, binascii.Error):
        raise ValidationError("이미지 데이터가 올바르지 않습니다.") from None
    mime = match[1]
    valid = ((mime == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
             or (mime == "image/jpeg" and data.startswith(b"\xff\xd8\xff"))
             or (mime == "image/webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP"))
    if not valid or not 12 <= len(data) <= MAX_IMAGE:
        raise ValidationError("이미지 형식과 5MB 이하 크기를 확인해주세요.")
    name = payload.get("name", "image")
    if not isinstance(name, str) or not 1 <= len(name) <= 200:
        raise ValidationError("이미지 파일 이름이 올바르지 않습니다.")
    key, digest = uuid.uuid4().hex, hashlib.sha256(data).hexdigest()
    with library.database() as db:
        tables(db)
        db.execute("INSERT INTO reference_assets VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (key, payload["id"], character, name, mime, digest, data))
        db.execute("INSERT INTO reference_targets VALUES (?, ?, ?, ?, ?)",
                   (key, item_kind, target_id, target_name, owner))
    return {"id": key, "character_id": character, "name": name, "mime": mime, "sha256": digest,
            "kind": item_kind, "target_id": target_id, "target_name": target_name, "owner_id": owner,
            "shot_ids": shot_ids, "role": BACKGROUND_ROLE if background else "appearance" if item_kind == "character" else item_kind,
            "note": note}


def asset(key):
    with library.database() as db:
        tables(db)
        row = db.execute("SELECT * FROM reference_assets WHERE id=?", (library.identifier(key),)).fetchone()
    if row is None:
        raise ValidationError("참조 이미지를 찾을 수 없습니다.")
    library.load(row["board_id"])
    return row


def manifest(board_id, selection, profile=None):
    board = library.load(board_id)
    if not isinstance(selection, list) or len(selection) > 9:
        raise ValidationError("레퍼런스 이미지는 종류에 관계없이 합쳐서 9장까지 추가할 수 있습니다.")
    if profile and ((profile["mode"] == "text" and selection)
                    or (profile["mode"] == "image" and selection)
                    or (profile["mode"] == "reference" and not selection)):
        raise ValidationError("이미지 사용 여부에 맞는 가이드를 선택해주세요.")
    result, seen = [], set()
    for index, item in enumerate(selection):
        if not isinstance(item, dict):
            raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
        row = asset(item.get("id"))
        target = metadata(row)
        role, note = item.get("role"), item.get("note", "")
        allowed_roles = ROLES if target["kind"] == "character" else (BACKGROUND_ROLE if target["kind"] == "background" else target["kind"],)
        if (row["board_id"] != board_id or row["id"] in seen or role not in allowed_roles
                or not isinstance(note, str) or len(note) > 1000):
            raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
        if (item.get("character_id", row["character_id"]) != row["character_id"]
                or any(key in item and item[key] != target[key] for key in target)):
            raise ValidationError("참조 대상이 원본 저장 항목과 다릅니다.")
        if target["kind"] == "other" and not note.strip():
            raise ValidationError("그 외 레퍼런스는 참고할 내용을 입력해주세요.")
        shot_ids = item.get("shot_ids", [])
        validate_scope(shot_ids, board)
        scope_mode = item.get("scope_mode", "selected" if shot_ids else "all")
        if scope_mode not in ("all", "selected") or (scope_mode == "selected") != bool(shot_ids):
            raise ValidationError("직접 적용할 컷을 하나 이상 선택해주세요.")
        seen.add(row["id"])
        label = f"<Picture {index + 1}>" if profile and profile["id"].startswith("minimax") else f"Image {index + 1}"
        result.append({"id": row["id"], "character_id": row["character_id"], "name": row["name"],
                       "mime": row["mime"], "sha256": row["sha256"], "role": role, "note": note,
                       **target, "shot_ids": shot_ids, "scope_mode": scope_mode,
                       "order": index + 1, "label": label, "guidance": ROLE_GUIDANCE[role]})
    groups = {}
    for item in result:
        key = target_key(item)
        scope = sorted(item["shot_ids"])
        if key in groups and groups[key] != scope:
            raise ValidationError("같은 대상의 이미지에는 동일한 적용 컷을 선택해주세요.")
        groups[key] = scope
    return result


def save(board_id, selection):
    checked = manifest(board_id, selection)
    with library.database() as db:
        tables(db)
        db.execute("INSERT OR REPLACE INTO reference_selections VALUES (?, ?)",
                   (board_id, json.dumps(checked, ensure_ascii=False)))
    return checked


def load(board_id):
    library.load(board_id)
    with library.database() as db:
        tables(db)
        row = db.execute("SELECT selection FROM reference_selections WHERE board_id=?", (board_id,)).fetchone()
    return json.loads(row[0]) if row else []


def package(conversion_id):
    from .prompt_renderer import export_text

    with library.database() as db:
        row = db.execute("SELECT board_id, result FROM conversions WHERE id=?",
                         (library.identifier(conversion_id),)).fetchone()
    if row is None:
        raise ValidationError("변환 결과를 찾을 수 없습니다.")
    library.load(row["board_id"])
    result = json.loads(row["result"])
    prompt_text = export_text(result)
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        manifest_items = []
        for item in result.get("references", []):
            image = asset(item["id"])
            if image["board_id"] != row["board_id"] or image["sha256"] != item["sha256"]:
                raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
            extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[image["mime"]]
            filename = f"references/{item['order']:02d}-{image['id']}.{extension}"
            archive.writestr(filename, image["data"])
            manifest_items.append({**item, "file": filename})
        archive.writestr("manifest.json", json.dumps(manifest_items, ensure_ascii=False, indent=2))
        archive.writestr("video-prompts.json", json.dumps(result, ensure_ascii=False, indent=2))
        archive.writestr("video-prompts.txt", prompt_text)
        archive.writestr("README.txt", "Attach references in manifest order for EACH clip. Use the specified model/mode.\n"
                         "Images have not been visually analyzed. This package does not submit video generation jobs.\n")
    return bundle.getvalue()
