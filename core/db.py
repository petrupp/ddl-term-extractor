"""SQLite 기반 용어사전 저장소 - 중복 제거(UPSERT) 및 누적 관리"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime

from core.extractor import HEADER

_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DB_DIR / "terms.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS terms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    term_name   TEXT,
    term_eng    TEXT UNIQUE,
    term_def    TEXT,
    domain_name TEXT,
    info_type   TEXT,
    data_type   TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_UPSERT_SQL = """
INSERT INTO terms (term_name, term_eng, term_def, domain_name, info_type, data_type, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(term_eng) DO UPDATE SET
    term_name   = CASE WHEN excluded.term_name != '' THEN excluded.term_name ELSE terms.term_name END,
    term_def    = CASE WHEN excluded.term_def  != '' THEN excluded.term_def  ELSE terms.term_def  END,
    domain_name = CASE WHEN excluded.domain_name != '' THEN excluded.domain_name ELSE terms.domain_name END,
    info_type   = CASE WHEN excluded.info_type != '' THEN excluded.info_type ELSE terms.info_type END,
    data_type   = CASE WHEN excluded.data_type != '' THEN excluded.data_type ELSE terms.data_type END,
    updated_at  = excluded.updated_at
"""

_HEADER_TO_COL = {
    "용어명": "term_name",
    "용어영문명": "term_eng",
    "용어정의": "term_def",
    "도메인명": "domain_name",
    "인포타입": "info_type",
    "데이터타입": "data_type",
}


def _ensure_db() -> Path:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


def _connect() -> sqlite3.Connection:
    db_path = _ensure_db()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_CREATE_SQL)
    conn.commit()
    return conn


def upsert_records(records: list[dict[str, str]]) -> tuple[int, int]:
    """레코드를 DB에 UPSERT. (신규 건수, 갱신 건수) 반환."""
    conn = _connect()
    try:
        before_count = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]

        now = datetime.now().isoformat()
        rows = [
            (
                r.get("용어명", ""),
                r.get("용어영문명", ""),
                r.get("용어정의", ""),
                r.get("도메인명", ""),
                r.get("인포타입", ""),
                r.get("데이터타입", ""),
                now,
            )
            for r in records
            if r.get("용어영문명", "").strip()
        ]

        conn.executemany(_UPSERT_SQL, rows)
        conn.commit()

        after_count = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]

        inserted = after_count - before_count
        updated = len(rows) - inserted
        return inserted, updated
    finally:
        conn.close()


def fetch_all() -> list[dict[str, str]]:
    """DB 전체 용어를 HEADER 딕셔너리 리스트로 반환."""
    conn = _connect()
    try:
        cur = conn.execute(
            "SELECT term_name, term_eng, term_def, domain_name, info_type, data_type "
            "FROM terms ORDER BY term_eng"
        )
        col_to_header = {v: k for k, v in _HEADER_TO_COL.items()}
        db_cols = ["term_name", "term_eng", "term_def", "domain_name", "info_type", "data_type"]

        return [
            {col_to_header[db_cols[i]]: (val or "") for i, val in enumerate(row)}
            for row in cur.fetchall()
        ]
    finally:
        conn.close()


def get_stats() -> dict[str, int]:
    """DB 통계 반환."""
    conn = _connect()
    try:
        total = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
        with_name = conn.execute(
            "SELECT COUNT(*) FROM terms WHERE term_name IS NOT NULL AND term_name != ''"
        ).fetchone()[0]
        return {"total": total, "with_name": with_name, "without_name": total - with_name}
    finally:
        conn.close()


def clear_all_terms() -> int:
    """누적된 모든 용어 행을 삭제하고, AUTOINCREMENT 시퀀스를 초기화. 삭제된 건수 반환."""
    conn = _connect()
    try:
        before = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
        conn.execute("DELETE FROM terms")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'terms'")
        conn.commit()
        return before
    finally:
        conn.close()
