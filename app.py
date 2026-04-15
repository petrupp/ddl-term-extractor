"""DDL → DA# 표준용어 사전 추출기  ·  Streamlit UI"""

import streamlit as st
import pandas as pd

from core.parser import parse_ddl
from core.extractor import tables_to_records, HEADER
from core.excel_writer import write_excel
from core.db import upsert_records, fetch_all, get_stats, clear_all_terms

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
    st.subheader("DB 전체 내보내기")
    if stats["total"] > 0:
        all_records = fetch_all()
        excel_all = write_excel(all_records)
        st.download_button(
            label=f"전체 {stats['total']:,}건 Excel 다운로드",
            data=excel_all,
            file_name="용어사전_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.caption("아직 추출된 용어가 없습니다.")

    st.divider()
    with st.expander("누적 데이터 초기화", expanded=False):
        st.caption("SQLite에 저장된 용어를 모두 삭제합니다. 되돌릴 수 없습니다.")
        confirm = st.checkbox("삭제를 확인했습니다", key="reset_confirm")
        if st.button(
            "누적 데이터 전부 삭제",
            type="primary",
            disabled=not confirm or stats["total"] == 0,
            use_container_width=True,
            key="reset_btn",
        ):
            deleted = clear_all_terms()
            st.success(f"{deleted:,}건이 삭제되었습니다.")
            st.rerun()

# ── 메인 영역 ──
st.title("DDL → DA# 표준용어 사전 추출기")
st.caption("PostgreSQL DDL을 붙여넣거나 .sql 파일을 업로드하면 용어를 추출하여 DB에 누적 저장합니다.")

tab_paste, tab_upload = st.tabs(["DDL 붙여넣기", "파일 업로드"])

ddl_text = ""

with tab_paste:
    ddl_text_input = st.text_area(
        "DDL을 붙여넣으세요 (CREATE TABLE + COMMENT ON)",
        height=350,
        placeholder="CREATE TABLE resources (\n    resource_id VARCHAR(50) NOT NULL,\n    ...\n);\nCOMMENT ON TABLE resources IS '자원마스터';",
    )
    if ddl_text_input:
        ddl_text = ddl_text_input

with tab_upload:
    uploaded = st.file_uploader("SQL 파일 업로드", type=["sql", "txt", "ddl"])
    if uploaded is not None:
        ddl_text = uploaded.read().decode("utf-8")
        st.code(ddl_text[:2000] + ("..." if len(ddl_text) > 2000 else ""), language="sql")

if st.button("추출하기", type="primary", use_container_width=True):
    if not ddl_text.strip():
        st.warning("DDL을 입력해주세요.")
    else:
        with st.spinner("DDL 파싱 중..."):
            tables = parse_ddl(ddl_text)

        if not tables:
            st.error("CREATE TABLE 구문을 찾을 수 없습니다. DDL을 확인해주세요.")
        else:
            records = tables_to_records(tables)
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
                label="이번 추출 결과 Excel 다운로드 (.xlsx)",
                data=excel_bytes,
                file_name="용어사전_추출결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
