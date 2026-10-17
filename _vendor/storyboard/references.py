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

ROLES = ("face", "body", "outfit", "expression", "detail")
BACKGROUND_ROLE = "environment"
MAX_IMAGE = 5_000_000


def tables(db):
    db.execute("CREATE TABLE IF NOT EXISTS reference_assets "
               "(id TEXT PRIMARY KEY, board_id TEXT, character_id TEXT, name TEXT, mime TEXT, sha256 TEXT, data BLOB)")
    db.execute("CREATE TABLE IF NOT EXISTS reference_selections (board_id TEXT PRIMARY KEY, selection TEXT)")


def upload(payload):
    board = library.load(payload.get("id"))
    background = payload.get("kind", "character") == "background"
    if payload.get("kind", "character") not in ("character", "background"):
        raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
    character = "" if background else payload.get("character_id")
    if background and payload.get("character_id") not in (None, ""):
        raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
    if not background and character not in [c["id"] for c in board["brief"]["characters"]]:
        raise ValidationError("참조 이미지의 캐릭터가 원본 콘티와 다릅니다.")
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
    return {"id": key, "character_id": character, "name": name, "mime": mime, "sha256": digest,
            "role": BACKGROUND_ROLE if background else "face", "note": ""}


def asset(key):
    with library.database() as db:
        tables(db)
        row = db.execute("SELECT * FROM reference_assets WHERE id=?", (library.identifier(key),)).fetchone()
    if row is None:
        raise ValidationError("참조 이미지를 찾을 수 없습니다.")
    library.load(row["board_id"])
    return row


def manifest(board_id, selection, profile=None):
    library.load(board_id)
    if not isinstance(selection, list) or len(selection) > 9:
        raise ValidationError("캐릭터와 배경 참조 이미지는 합쳐서 9장 이내로 선택해주세요.")
    if profile and ((profile["mode"] == "text" and selection)
                    or (profile["mode"] == "image" and selection)
                    or (profile["mode"] == "reference" and not selection)):
        raise ValidationError("이미지 사용 여부에 맞는 가이드를 선택해주세요.")
    result, seen = [], set()
    for index, item in enumerate(selection):
        if not isinstance(item, dict):
            raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
        row = asset(item.get("id"))
        role, note = item.get("role"), item.get("note", "")
        allowed_roles = (BACKGROUND_ROLE,) if row["character_id"] == "" else ROLES
        if (row["board_id"] != board_id or row["id"] in seen or role not in allowed_roles
                or not isinstance(note, str) or len(note) > 1000):
            raise ValidationError("참조 이미지 설정이 올바르지 않습니다.")
        seen.add(row["id"])
        label = f"<Picture {index + 1}>" if profile and profile["id"].startswith("minimax") else f"Image {index + 1}"
        result.append({"id": row["id"], "character_id": row["character_id"], "name": row["name"],
                       "mime": row["mime"], "sha256": row["sha256"], "role": role, "note": note,
                       "order": index + 1, "label": label})
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
