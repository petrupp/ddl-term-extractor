"""DDL → DA# 표준용어 사전 추출기  ·  Streamlit UI"""

import streamlit as st
import pandas as pd

from core.parser import parse_ddl
from core.extractor import tables_to_records, HEADER
from core.excel_writer import (
    write_excel,
    write_domains_excel,
    domain_rows_to_sheet_dicts,
)
from core.db import (
    upsert_records,
    fetch_all,
    get_stats,
    clear_all_terms,
    clear_all_domains,
    fetch_all_domains,
    fetch_domain_catalog_for_match,
    replace_all_domains,
    reset_domains_to_defaults,
)

st.set_page_config(
    page_title="DDL 용어사전 추출기",
    page_icon="📋",
    layout="wide",
)

# ── 사이드바: DB 현황 ──
with st.sidebar:
    st.header("용어사전 DB 현황")
    stats = get_stats()
    st.metric("누적 용어 수", f"{stats['total']:,}건")
    col1, col2 = st.columns(2)
    col1.metric("용어명 있음", f"{stats['with_name']:,}")
    col2.metric("용어명 없음", f"{stats['without_name']:,}")

    st.divider()
    st.subheader("Excel 다운로드")
    dom_rows = fetch_all_domains()

    st.caption("표준용어사전 (DB 누적)")
    if stats["total"] > 0:
        all_records = fetch_all()
        excel_terms = write_excel(all_records)
        st.download_button(
            label=f"표준용어사전 다운로드 ({stats['total']:,}건)",
            data=excel_terms,
            file_name="표준용어사전.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_terms_sidebar",
        )
    else:
        st.caption("누적된 용어가 없습니다.")

    st.caption("표준도메인사전")
    if dom_rows:
        dom_excel = write_domains_excel(domain_rows_to_sheet_dicts(dom_rows))
        st.download_button(
            label=f"표준도메인사전 다운로드 ({len(dom_rows):,}건)",
            data=dom_excel,
            file_name="표준도메인사전.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_domains_sidebar",
        )
    else:
        st.caption("등록된 도메인 행이 없습니다.")

    st.divider()
    with st.expander("누적 데이터 초기화", expanded=False):
        st.markdown("**표준용어사전** — DDL 추출 누적 데이터 (`terms`)")
        st.caption("삭제 후 되돌릴 수 없습니다.")
        confirm_terms = st.checkbox("표준용어사전 삭제에 동의합니다", key="reset_confirm_terms")
        if st.button(
            "표준용어사전 데이터 삭제",
            type="primary",
            disabled=not confirm_terms or stats["total"] == 0,
            use_container_width=True,
            key="reset_btn_terms",
        ):
            deleted = clear_all_terms()
            st.success(f"표준용어 {deleted:,}건을 삭제했습니다.")
            st.rerun()

        st.markdown("**표준도메인사전** — `standard_domains`")
        st.caption("비운 뒤에는 이 탭에서 저장하거나 「PostgreSQL 기본 세트로 복원」을 사용하세요.")
        confirm_domains = st.checkbox("표준도메인사전 삭제에 동의합니다", key="reset_confirm_domains")
        dom_n = len(dom_rows)
        if st.button(
            "표준도메인사전 데이터 삭제",
            type="primary",
            disabled=not confirm_domains or dom_n == 0,
            use_container_width=True,
            key="reset_btn_domains",
        ):
            deleted_d = clear_all_domains()
            st.success(f"표준도메인 {deleted_d:,}건을 삭제했습니다.")
            st.rerun()

# ── 메인 영역 ──
st.title("DDL → DA# 표준용어 사전 추출기")
st.caption(
    "PostgreSQL DDL을 파싱해 용어를 추출하고, 표준 도메인 사전과 맞으면 도메인명·인포타입을 채우며, "
    "데이터타입은 DDL의 실제 타입 문자열을 사용합니다."
)

tab_extract, tab_domains = st.tabs(["용어 추출", "표준 도메인 사전"])

with tab_extract:
    st.caption("DDL 붙여넣기 또는 파일 업로드 후 추출하면 SQLite에 누적 저장됩니다.")

    tab_paste, tab_upload = st.tabs(["DDL 붙여넣기", "파일 업로드"])

    ddl_text = ""

    with tab_paste:
        ddl_text_input = st.text_area(
            "DDL을 붙여넣으세요 (CREATE TABLE + COMMENT ON)",
            height=350,
            placeholder="CREATE TABLE resources (\n    resource_id VARCHAR(50) NOT NULL,\n    ...\n);\nCOMMENT ON TABLE resources IS '자원마스터';",
            key="ddl_paste",
        )
        if ddl_text_input:
            ddl_text = ddl_text_input

    with tab_upload:
        uploaded = st.file_uploader("SQL 파일 업로드", type=["sql", "txt", "ddl"], key="ddl_upload")
        if uploaded is not None:
            ddl_text = uploaded.read().decode("utf-8")
            st.code(ddl_text[:2000] + ("..." if len(ddl_text) > 2000 else ""), language="sql")

    if st.button("추출하기", type="primary", use_container_width=True, key="btn_extract"):
        if not ddl_text.strip():
            st.warning("DDL을 입력해주세요.")
        else:
            with st.spinner("DDL 파싱 중..."):
                tables = parse_ddl(ddl_text)

            if not tables:
                st.error("CREATE TABLE 구문을 찾을 수 없습니다. DDL을 확인해주세요.")
            else:
                catalog = fetch_domain_catalog_for_match()
                records = tables_to_records(tables, domain_catalog=catalog)
                inserted, updated = upsert_records(records)

                total_tables = len(tables)
                total_cols = len(records)
                st.success(
                    f"총 {total_tables}개 테이블, {total_cols}개 컬럼 파싱 완료  →  "
                    f"**{inserted}건 신규 추가**, **{updated}건 갱신** (중복 제거)"
                )

                df = pd.DataFrame(records, columns=HEADER)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    height=min(40 * len(df) + 60, 600),
                )

                excel_bytes = write_excel(records)
                st.download_button(
                    label=f"표준용어사전 다운로드 (이번 추출 {len(records):,}건)",
                    data=excel_bytes,
                    file_name="표준용어사전_이번추출.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_extract",
                )

with tab_domains:
    st.markdown(
        "한글 용어명에서 뽑힌 **접미 도메인명**(예: 일자, ID, 여부)과 컬럼의 **PostgreSQL 기준 타입**이 "
        "아래 **데이터타입** 컬럼과 일치하면, 추출 결과의 **도메인명·인포타입**을 이 정의로 채웁니다. "
        "표준도메인의 **데이터타입**은 DDL 전체 표기가 아니라 기준 타입(VARCHAR, DATE 등)입니다. "
        "**인포타입**을 비우면 자동 생성 규칙을 사용합니다."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("PostgreSQL 기본 세트로 복원", type="secondary", key="btn_domain_reset"):
            n = reset_domains_to_defaults()
            st.success(f"기본 {n}건으로 복원했습니다.")
            st.rerun()
    with c2:
        dom_n = len(fetch_all_domains())
        st.caption(f"현재 등록: **{dom_n}**건 · Excel은 왼쪽 사이드바에서 받을 수 있습니다.")

    rows = fetch_all_domains()
    df_dom = pd.DataFrame(rows)
    if "id" in df_dom.columns:
        df_dom = df_dom.drop(columns=["id"])

    preferred = [
        "domain_group",
        "domain_name",
        "data_type",
        "length",
        "info_type",
        "note",
    ]
    df_dom = df_dom[[c for c in preferred if c in df_dom.columns]]

    edited = st.data_editor(
        df_dom,
        num_rows="dynamic",
        column_config={
            "domain_group": st.column_config.TextColumn(
                "도메인그룹",
                help="예: 금액·금융 — 같은 그룹에 가격·가액·비용 등 도메인명을 둘 수 있음",
            ),
            "domain_name": st.column_config.TextColumn("도메인명", help="용어명 접미어와 동일해야 매칭"),
            "data_type": st.column_config.TextColumn(
                "데이터타입",
                help="PostgreSQL 기준 타입(VARCHAR, INTEGER, DATE 등). DDL 컬럼의 기본 타입과 같아야 매칭됩니다.",
            ),
            "length": st.column_config.NumberColumn("길이", min_value=0, step=1, format="%d"),
            "info_type": st.column_config.TextColumn("인포타입", help="비우면 도메인+약어+길이로 생성"),
            "note": st.column_config.TextColumn("비고"),
        },
        use_container_width=True,
        hide_index=True,
        key="editor_domains",
    )

    if st.button("표준 도메인 저장", type="primary", use_container_width=True, key="btn_save_domains"):
        recs = edited.to_dict("records")
        n = replace_all_domains(recs)
        st.success(f"{n}건 저장했습니다.")
        st.rerun()
