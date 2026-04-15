"""파싱된 TableInfo를 DA# 표준용어 사전 양식으로 변환

출력 컬럼: 용어명, 용어영문명, 용어정의, 도메인명, 인포타입, 데이터타입
"""

from __future__ import annotations

import re

from core.parser import TableInfo, ColumnInfo


HEADER = [
    "용어명",
    "용어영문명",
    "용어정의",
    "도메인명",
    "인포타입",
    "데이터타입",
]

# ---------------------------------------------------------------------------
# PostgreSQL 타입 정규화 (SERIAL 계열 등)
# ---------------------------------------------------------------------------
_PG_NORMALIZE: dict[str, str] = {
    "CHARACTER VARYING": "VARCHAR",
    "CHARACTER": "CHAR",
    "INT": "INTEGER",
    "INT4": "INTEGER",
    "INT8": "BIGINT",
    "INT2": "SMALLINT",
    "SERIAL": "INTEGER",
    "BIGSERIAL": "BIGINT",
    "SMALLSERIAL": "SMALLINT",
    "FLOAT4": "REAL",
    "FLOAT8": "DOUBLE PRECISION",
    "DECIMAL": "NUMERIC",
    "BOOL": "BOOLEAN",
    "TIMESTAMPTZ": "TIMESTAMP",
    "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
    "TIMESTAMP WITH TIME ZONE": "TIMESTAMP",
}

# ---------------------------------------------------------------------------
# PostgreSQL 타입 약어 (인포타입 생성용)
# ---------------------------------------------------------------------------
_TYPE_ABBR: dict[str, str] = {
    "VARCHAR": "VC",
    "CHAR": "CH",
    "TEXT": "TX",
    "INTEGER": "INT",
    "BIGINT": "BIG",
    "SMALLINT": "SI",
    "NUMERIC": "NM",
    "REAL": "RL",
    "DOUBLE PRECISION": "DP",
    "BOOLEAN": "BL",
    "DATE": "DT",
    "TIMESTAMP": "TS",
    "TIME": "TM",
    "BYTEA": "BY",
    "JSON": "JS",
    "JSONB": "JB",
    "UUID": "UID",
}

# ---------------------------------------------------------------------------
# 도메인명 추출용 접미어 사전 (긴 것부터 매칭)
# ---------------------------------------------------------------------------
_DOMAIN_SUFFIXES: list[str] = [
    "일련번호", "순번", "번호",
    "IP주소", "주소",
    "일시", "일자", "날짜", "시각",
    "금액", "단가",
    "비율", "율",
    "수량", "건수", "횟수", "량", "수",
    "기록",
    "여부",
    "코드",
    "구분",
    "유형",
    "상태",
    "내용", "설명", "비고",
    "명",
    "ID",
    "NO",
]


def _strip_parens(text: str) -> str:
    """괄호 안 보충 설명 제거: '자원ID(그룹내유일)' → '자원ID'"""
    return re.sub(r"\([^)]*\)", "", text).strip()


def _extract_domain(korean_name: str) -> str:
    """한글 용어명에서 도메인명(접미어) 추출"""
    clean = _strip_parens(korean_name)

    for suffix in _DOMAIN_SUFFIXES:
        if clean.endswith(suffix):
            return suffix

    return clean


def _format_pg_type(col: ColumnInfo) -> tuple[str, str]:
    """ColumnInfo → (PostgreSQL 타입 전체 문자열, 정규화된 기본 타입명) 반환

    예: VARCHAR, 50 → ("VARCHAR(50)", "VARCHAR")
        INTEGER, None → ("INTEGER", "INTEGER")
        NUMERIC, 5, 1 → ("NUMERIC(5,1)", "NUMERIC")
    """
    raw = col.data_type.upper()
    base = _PG_NORMALIZE.get(raw, raw)

    if col.length is not None and col.scale is not None:
        full = f"{base}({col.length},{col.scale})"
    elif col.length is not None:
        full = f"{base}({col.length})"
    else:
        full = base

    return full, base


def _build_infotype(domain: str, pg_base: str, length: int | None, scale: int | None) -> str:
    """인포타입 생성: 도메인명 + 타입약어 + 길이정보

    예: ID + VC + 50 → IDVC50
        일시 + TS → 일시TS
        량 + NM + 5,1 → 량NM5.1
        금액 + NM → 금액NM
        여부 + CH + 1 → 여부CH1
    """
    abbr = _TYPE_ABBR.get(pg_base, pg_base[:2])

    if length is not None and scale is not None:
        size_part = f"{length}.{scale}"
    elif length is not None:
        size_part = str(length)
    else:
        size_part = ""

    return f"{domain}{abbr}{size_part}"


def tables_to_records(tables: list[TableInfo]) -> list[dict[str, str]]:
    """TableInfo 리스트를 DA# 용어사전 양식 딕셔너리 리스트로 변환"""
    rows: list[dict[str, str]] = []

    for table in tables:
        for col in table.columns:
            comment = col.column_comment or ""
            term_name = _strip_parens(comment)
            term_eng = col.column_name.lower()

            pg_full, pg_base = _format_pg_type(col)
            infotype = _build_infotype(
                _extract_domain(comment) if comment else "",
                pg_base, col.length, col.scale,
            )

            rows.append({
                "용어명": term_name,
                "용어영문명": term_eng,
                "용어정의": "",
                "도메인명": "",
                "인포타입": infotype,
                "데이터타입": pg_full,
            })

    return rows
