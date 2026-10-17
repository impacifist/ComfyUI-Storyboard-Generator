"""Local immutable storyboard snapshots and recoverable deletion."""

import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from .engine import now, validate_document
from .schema import ValidationError

ROOT = Path(__file__).resolve().parent.parent


@contextmanager
def database():
    folder = ROOT / "storage" / "library"
    folder.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(folder / "storyboards.sqlite3", timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS boards "
                           "(id TEXT PRIMARY KEY, title TEXT, saved_at TEXT, document TEXT, deleted INTEGER DEFAULT 0)")
        connection.execute("CREATE TABLE IF NOT EXISTS conversions "
                           "(id TEXT PRIMARY KEY, board_id TEXT, created_at TEXT, result TEXT)")
        with connection:
            yield connection
    finally:
        connection.close()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
        raise ValidationError("올바른 콘티 ID가 필요합니다.")
    return value


def save(document):
    validate_document(document)
    encoded = json.dumps(document, ensure_ascii=False, allow_nan=False)
    if len(encoded.encode("utf-8")) > 16_000_000:
        raise ValidationError("저장할 콘티가 너무 큽니다.")
    key, timestamp = uuid.uuid4().hex, now()
    with database() as db:
        db.execute("INSERT INTO boards VALUES (?, ?, ?, ?, 0)",
                   (key, document["brief"]["title"], timestamp, encoded))
    return {"id": key, "title": document["brief"]["title"], "saved_at": timestamp}


def listing(deleted=False):
    if type(deleted) is not bool:
        raise ValidationError("휴지통 선택은 참/거짓이어야 합니다.")
    with database() as db:
        rows = db.execute("SELECT id, title, saved_at, document FROM boards WHERE deleted=? "
                          "ORDER BY saved_at DESC, rowid DESC", (int(deleted),)).fetchall()
    result = []
    for row in rows:
        document = json.loads(row["document"])
        result.append({"id": row["id"], "title": row["title"], "saved_at": row["saved_at"],
                       "shots": len(document["story"]["shots"]),
                       "duration": sum(s["duration"] for s in document["story"]["shots"])})
    return result


def load(key):
    with database() as db:
        row = db.execute("SELECT document FROM boards WHERE id=? AND deleted=0", (identifier(key),)).fetchone()
    if row is None:
        raise ValidationError("저장된 콘티가 없거나 휴지통에 있습니다.")
    document = json.loads(row["document"])
    validate_document(document)
    return document


def trash(key, deleted=True):
    with database() as db:
        cursor = db.execute("UPDATE boards SET deleted=? WHERE id=? AND deleted=?",
                            (int(deleted), identifier(key), int(not deleted)))
        if cursor.rowcount != 1:
            raise ValidationError("콘티를 찾을 수 없거나 이미 처리되었습니다.")


def save_conversion(key, result):
    with database() as db:
        if not db.execute("SELECT 1 FROM boards WHERE id=? AND deleted=0", (identifier(key),)).fetchone():
            raise ValidationError("원본 콘티가 휴지통에 있어 변환을 저장할 수 없습니다.")
        conversion_id = uuid.uuid4().hex
        db.execute("INSERT INTO conversions VALUES (?, ?, ?, ?)",
                   (conversion_id, key, now(), json.dumps(result, ensure_ascii=False, allow_nan=False)))
    return conversion_id


def conversions(key):
    load(key)
    with database() as db:
        rows = db.execute("SELECT id, created_at, result FROM conversions WHERE board_id=? "
                          "ORDER BY rowid DESC", (identifier(key),)).fetchall()
    return [{"id": r["id"], "created_at": r["created_at"], "result": json.loads(r["result"])} for r in rows]
