"""PostgreSQL DDL 파서 - CREATE TABLE + COMMENT ON + 인라인 주석 파싱"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ColumnInfo:
    table_name: str
    table_comment: str = ""
    column_name: str = ""
    data_type: str = ""
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    nullable: bool = True
    default_value: str | None = None
    is_pk: bool = False
    column_comment: str = ""


@dataclass
class TableInfo:
    table_name: str
    table_comment: str = ""
    columns: list[ColumnInfo] = field(default_factory=list)
    pk_columns: list[str] = field(default_factory=list)


_SERIAL_MAP = {
    "SERIAL": ("INTEGER", None),
    "BIGSERIAL": ("BIGINT", None),
    "SMALLSERIAL": ("SMALLINT", None),
}

_RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\S+)\s*\((.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)

_RE_COMMENT_TABLE = re.compile(
    r"COMMENT\s+ON\s+TABLE\s+(\S+)\s+IS\s+'((?:[^']|'')*?)'\s*;",
    re.IGNORECASE,
)

_RE_COMMENT_COLUMN = re.compile(
    r"COMMENT\s+ON\s+COLUMN\s+(\S+)\.(\S+)\s+IS\s+'((?:[^']|'')*?)'\s*;",
    re.IGNORECASE,
)

_RE_INLINE_PK = re.compile(r"\bPRIMARY\s+KEY\b", re.IGNORECASE)

_RE_TABLE_PK = re.compile(
    r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.IGNORECASE
)

_RE_TYPE = re.compile(
    r"^(\w+)"
    r"(?:\((\d+)(?:\s*,\s*(\d+))?\))?",
    re.IGNORECASE,
)


def _parse_type(raw: str) -> tuple[str, int | None, int | None]:
    raw = raw.strip().upper()

    if raw in _SERIAL_MAP:
        dtype, length = _SERIAL_MAP[raw]
        return dtype, length, None

    m = _RE_TYPE.match(raw)
    if not m:
        return raw, None, None

    dtype = m.group(1)
    if dtype in _SERIAL_MAP:
        dtype, _ = _SERIAL_MAP[dtype]

    length = int(m.group(2)) if m.group(2) else None
    scale = int(m.group(3)) if m.group(3) else None
    return dtype, length, scale


def _strip_inline_comments(body: str) -> tuple[str, dict[str, str]]:
    """CREATE TABLE 본문에서 인라인 주석(-- ...)을 제거하고, 컬럼명→주석 매핑을 반환.

    반환: (주석 제거된 본문, {컬럼명(소문자): 주석텍스트})
    """
    inline_comments: dict[str, str] = {}
    cleaned_lines: list[str] = []

    skip_keywords = frozenset((
        "PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "CONSTRAINT",
        "EXCLUDE", "--", "",
    ))

    for line in body.split("\n"):
        dash_pos = line.find("--")
        if dash_pos >= 0:
            before = line[:dash_pos]
            comment_text = line[dash_pos + 2:].strip()

            tokens = before.strip().rstrip(",").split()
            if tokens and tokens[0].upper() not in skip_keywords:
                col_name = tokens[0].strip('"').lower()
                if comment_text:
                    inline_comments[col_name] = comment_text

            cleaned_lines.append(before)
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines), inline_comments


def _split_column_defs(body: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []

    for ch in body:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)

    return parts


def _parse_column_def(line: str, table_name: str) -> ColumnInfo | None:
    line = line.strip()
    if not line:
        return None

    constraint_keywords = (
        "PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "CONSTRAINT", "EXCLUDE",
    )
    first_word = line.split()[0].upper()
    if first_word in constraint_keywords:
        return None

    tokens = line.split()
    if len(tokens) < 2:
        return None

    col_name = tokens[0].strip('"')
    rest = " ".join(tokens[1:])

    inline_pk = bool(_RE_INLINE_PK.search(rest))
    rest = _RE_INLINE_PK.sub("", rest).strip()

    # UNIQUE 제약조건 제거
    rest = re.sub(r"\bUNIQUE\b", "", rest, flags=re.IGNORECASE).strip()

    nullable = True
    if re.search(r"\bNOT\s+NULL\b", rest, re.IGNORECASE):
        nullable = False
        rest = re.sub(r"\bNOT\s+NULL\b", "", rest, flags=re.IGNORECASE).strip()
    elif re.search(r"\bNULL\b", rest, re.IGNORECASE):
        rest = re.sub(r"\bNULL\b", "", rest, count=1, flags=re.IGNORECASE).strip()

    default_value = None
    dm = re.search(r"\bDEFAULT\s+(.+)$", rest, re.IGNORECASE)
    if dm:
        default_value = dm.group(1).strip().rstrip(",")
        rest = rest[: dm.start()].strip()

    type_str = rest.split()[0] if rest.split() else ""
    type_with_len = rest.strip()
    paren = type_with_len.find("(")
    if paren != -1:
        end = type_with_len.find(")", paren)
        type_str = type_with_len[: end + 1] if end != -1 else type_with_len
    else:
        type_str = type_with_len.split()[0] if type_with_len else ""

    dtype, length, scale = _parse_type(type_str)

    col = ColumnInfo(
        table_name=table_name,
        column_name=col_name,
        data_type=dtype,
        length=length,
        scale=scale,
        nullable=nullable,
        default_value=default_value,
        is_pk=inline_pk,
    )
    return col


def parse_ddl(ddl_text: str) -> list[TableInfo]:
    """DDL 전체 텍스트를 파싱하여 TableInfo 리스트 반환"""
    tables: dict[str, TableInfo] = {}

    # 1) CREATE TABLE 파싱 (인라인 주석 분리 후 처리)
    for m in _RE_CREATE_TABLE.finditer(ddl_text):
        raw_name = m.group(1).strip('"').lower()
        body = m.group(2)

        cleaned_body, inline_comments = _strip_inline_comments(body)

        table = TableInfo(table_name=raw_name)
        parts = _split_column_defs(cleaned_body)

        for part in parts:
            pk_match = _RE_TABLE_PK.search(part)
            if pk_match:
                pk_cols = [c.strip().strip('"').lower() for c in pk_match.group(1).split(",")]
                table.pk_columns.extend(pk_cols)
                continue

            col = _parse_column_def(part, raw_name)
            if col:
                # 인라인 주석을 우선 채워놓기 (COMMENT ON이 있으면 나중에 덮어씀)
                ic = inline_comments.get(col.column_name.lower(), "")
                if ic:
                    col.column_comment = ic
                table.columns.append(col)

        tables[raw_name] = table

    # 2) PK 플래그 갱신
    for t in tables.values():
        for col in t.columns:
            if col.column_name.lower() in [p.lower() for p in t.pk_columns]:
                col.is_pk = True

    # 3) COMMENT ON TABLE
    for m in _RE_COMMENT_TABLE.finditer(ddl_text):
        tname = m.group(1).strip('"').lower()
        comment = m.group(2).replace("''", "'")
        if tname in tables:
            tables[tname].table_comment = comment

    # 4) COMMENT ON COLUMN (인라인 주석보다 우선)
    for m in _RE_COMMENT_COLUMN.finditer(ddl_text):
        tname = m.group(1).strip('"').lower()
        cname = m.group(2).strip('"').lower()
        comment = m.group(3).replace("''", "'")
        if tname in tables:
            for col in tables[tname].columns:
                if col.column_name.lower() == cname:
                    col.column_comment = comment
                    col.table_comment = tables[tname].table_comment

    # table_comment를 모든 컬럼에 전파
    for t in tables.values():
        for col in t.columns:
            if not col.table_comment:
                col.table_comment = t.table_comment

    return list(tables.values())
