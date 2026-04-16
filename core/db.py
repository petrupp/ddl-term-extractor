"""SQLite term dictionary storage (UPSERT, accumulative)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DB_DIR / "terms.db"
_SEED_PATH = Path(__file__).resolve().parent / "domain_seed.json"

_CREATE_META_SQL = """
CREATE TABLE IF NOT EXISTS app_meta (
    k TEXT PRIMARY KEY,
    v TEXT
)
"""

_CREATE_DOMAINS_SQL = """
CREATE TABLE IF NOT EXISTS standard_domains (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_group    TEXT,
    domain_name     TEXT NOT NULL,
    data_type       TEXT NOT NULL,
    length          INTEGER,
    scale           INTEGER,
    info_type       TEXT,
    note            TEXT
)
"""

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
    "\uC6A9\uC5B4\uBA85": "term_name",
    "\uC6A9\uC5B4\uC601\uBB38\uBA85": "term_eng",
    "\uC6A9\uC5B4\uC815\uC758": "term_def",
    "\uB3C4\uBA54\uC778\uBA85": "domain_name",
    "\uC778\uD3EC\uD0C0\uC785": "info_type",
    "\uB370\uC774\uD130\uD0C0\uC785": "data_type",
}


def _load_default_domain_seed() -> list[
    tuple[str, str, str, int | None, int | None, str, str | None]
]:
    raw = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    out: list[tuple[str, str, str, int | None, int | None, str, str | None]] = []
    for row in raw:
        g, n, dt, lg, sc, it, note = row
        out.append((g, n, dt, lg, sc, it, note))
    return out


_DEFAULT_DOMAIN_SEED = _load_default_domain_seed()


def _ensure_db() -> Path:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


def _connect() -> sqlite3.Connection:
    db_path = _ensure_db()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_CREATE_SQL)
    conn.execute(_CREATE_META_SQL)
    conn.execute(_CREATE_DOMAINS_SQL)
    conn.commit()
    _migrate_domains_schema(conn)
    _ensure_domain_seed_once(conn)
    return conn


def _migrate_domains_schema(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA table_info(standard_domains)")
    cols = {row[1] for row in cur.fetchall()}
    if not cols:
        return
    if "domain_group" not in cols:
        conn.execute("ALTER TABLE standard_domains ADD COLUMN domain_group TEXT")
        conn.commit()
        cols.add("domain_group")
    if "pg_base_type" not in cols:
        return
    conn.executescript(
        """
        CREATE TABLE standard_domains__new (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_group    TEXT,
            domain_name     TEXT NOT NULL,
            data_type       TEXT NOT NULL,
            length          INTEGER,
            scale           INTEGER,
            info_type       TEXT,
            note            TEXT
        );
        INSERT INTO standard_domains__new (
            domain_group, domain_name, data_type, length, scale, info_type, note
        )
        SELECT
            domain_group,
            domain_name,
            UPPER(TRIM(COALESCE(pg_base_type, ''))),
            length,
            scale,
            info_type,
            note
        FROM standard_domains;
        DROP TABLE standard_domains;
        ALTER TABLE standard_domains__new RENAME TO standard_domains;
        """
    )
    conn.commit()


def _ensure_domain_seed_once(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT 1 FROM app_meta WHERE k = 'domains_init_v1'").fetchone():
        return
    conn.executemany(
        """
        INSERT INTO standard_domains (domain_group, domain_name, data_type, length, scale, info_type, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        _DEFAULT_DOMAIN_SEED,
    )
    conn.execute(
        "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('domains_init_v1', '1')"
    )
    conn.commit()


def upsert_records(records: list[dict[str, str]]) -> tuple[int, int]:
    conn = _connect()
    try:
        before_count = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
        now = datetime.now().isoformat()
        rows = [
            (
                r.get("\uC6A9\uC5B4\uBA85", ""),
                r.get("\uC6A9\uC5B4\uC601\uBB38\uBA85", ""),
                r.get("\uC6A9\uC5B4\uC815\uC758", ""),
                r.get("\uB3C4\uBA54\uC778\uBA85", ""),
                r.get("\uC778\uD3EC\uD0C0\uC785", ""),
                r.get("\uB370\uC774\uD130\uD0C0\uC785", ""),
                now,
            )
            for r in records
            if r.get("\uC6A9\uC5B4\uC601\uBB38\uBA85", "").strip()
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
    conn = _connect()
    try:
        before = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
        conn.execute("DELETE FROM terms")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'terms'")
        conn.commit()
        return before
    finally:
        conn.close()


def clear_all_domains() -> int:
    """Delete all standard_domains rows; return count. Keeps app_meta (no auto re-seed)."""
    conn = _connect()
    try:
        before = conn.execute("SELECT COUNT(*) FROM standard_domains").fetchone()[0]
        conn.execute("DELETE FROM standard_domains")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'standard_domains'")
        conn.commit()
        return before
    finally:
        conn.close()


def _to_opt_int(val: object) -> int | None:
    if val is None or val == "":
        return None
    try:
        if isinstance(val, float):
            import math

            if math.isnan(val):
                return None
        return int(float(val))
    except (TypeError, ValueError):
        return None


def fetch_all_domains() -> list[dict]:
    conn = _connect()
    try:
        cur = conn.execute(
            "SELECT id, domain_group, domain_name, data_type, length, info_type, note "
            "FROM standard_domains ORDER BY COALESCE(domain_group,''), domain_name, data_type, length"
        )
        cols = [
            "id",
            "domain_group",
            "domain_name",
            "data_type",
            "length",
            "info_type",
            "note",
        ]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def fetch_domain_catalog_for_match() -> list[dict]:
    conn = _connect()
    try:
        cur = conn.execute(
            "SELECT domain_name, data_type, length, info_type "
            "FROM standard_domains ORDER BY domain_name, data_type"
        )
        out: list[dict] = []
        for domain_name, data_type, length, info_type in cur.fetchall():
            out.append({
                "domain_name": domain_name or "",
                "data_type": (data_type or "").upper(),
                "length": length,
                "info_type": info_type,
            })
        return out
    finally:
        conn.close()


def replace_all_domains(records: list[dict]) -> int:
    conn = _connect()
    try:
        conn.execute("DELETE FROM standard_domains")
        n = 0
        ins = """
        INSERT INTO standard_domains (domain_group, domain_name, data_type, length, scale, info_type, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        for r in records:
            dn = str(r.get("domain_name", "") or "").strip()
            dt = str(r.get("data_type", "") or "").strip()
            if not dn or not dt:
                continue
            dg = str(r.get("domain_group", "") or "").strip() or None
            length = _to_opt_int(r.get("length"))
            it = str(r.get("info_type", "") or "").strip() or None
            note = str(r.get("note", "") or "").strip() or None
            conn.execute(ins, (dg, dn, dt.upper(), length, None, it, note))
            n += 1
        conn.commit()
        return n
    finally:
        conn.close()


def reset_domains_to_defaults() -> int:
    conn = _connect()
    try:
        conn.execute("DELETE FROM standard_domains")
        conn.executemany(
            """
            INSERT INTO standard_domains (domain_group, domain_name, data_type, length, scale, info_type, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            _DEFAULT_DOMAIN_SEED,
        )
        conn.commit()
        return len(_DEFAULT_DOMAIN_SEED)
    finally:
        conn.close()
