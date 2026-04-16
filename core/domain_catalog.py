"""표준도메인사전 매칭 — 용어 추출 시 도메인명·인포타입·데이터타입 결정"""

from __future__ import annotations

from typing import Any


def match_domain_row(
    extracted_domain: str,
    pg_full: str,
    pg_base: str,
    length: int | None,
    scale: int | None,
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """추출된 접미 도메인명 + PG 타입으로 카탈로그에서 가장 구체적으로 맞는 행을 고른다."""
    if not extracted_domain or not rows:
        return None

    pg_base_u = pg_base.upper()
    best: tuple[int, dict[str, Any]] | None = None

    for r in rows:
        if (r.get("domain_name") or "") != extracted_domain:
            continue
        if (r.get("data_type") or "").upper() != pg_base_u:
            continue

        rl = r.get("length")
        if rl is not None and rl != length:
            continue

        spec = 2 if rl is not None else 0
        if best is None or spec > best[0]:
            best = (spec, r)

    return best[1] if best else None


def apply_domain_row(
    row: dict[str, Any],
    pg_full: str,
    pg_base: str,
    length: int | None,
    scale: int | None,
) -> tuple[str, str, str]:
    """매칭된 표준도메인 행 → (도메인명, 데이터타입, 인포타입)"""
    dname = row.get("domain_name") or ""
    dtype = pg_full
    if dname:
        itype = f"{dname}{pg_full}"
    else:
        from core.extractor import _build_infotype

        itype = _build_infotype("", pg_base, length, scale)

    return dname, dtype, itype
