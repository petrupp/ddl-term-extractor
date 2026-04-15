# DDL 용어사전 추출기 (ddl-term-extractor)

PostgreSQL DDL(`CREATE TABLE`, `COMMENT ON`, 인라인 `--` 주석)을 파싱해 DA# 표준용어 사전에 넣기 좋은 형태로 정리하고, SQLite에 누적 저장하며 Excel로 내보낼 수 있는 도구입니다.

## 목적

- 테이블·컬럼 정의와 주석을 한 번에 모아 **용어명·용어영문명·인포타입·데이터타입** 등을 자동으로 채운 시트를 만든다.
- 여러 번 DDL을 넣어도 **용어영문명(컬럼명) 기준**으로 중복을 제거하고 최신 정보로 갱신한다.
- 수만 건 규모도 SQLite·Excel로 관리 가능한 수준을 전제로 한다.

## 요구 사항

- **Python 3.12 이상** (권장)
- Windows 기준으로 동작을 확인했습니다.

## 설치 방법

프로젝트 루트(`ddl-term-extractor`)에서 다음 중 하나를 사용합니다.

### 방법 A: uv 사용 (권장)

[uv](https://github.com/astral-sh/uv)가 있으면 의존성과 가상환경이 한 번에 맞춰집니다.

```powershell
cd C:\my\ddl-term-extractor
uv sync
```

### 방법 B: pip 사용

```powershell
cd C:\my\ddl-term-extractor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

또는 `pyproject.toml` 기준:

```powershell
pip install -e .
```

## 실행 방법

### uv로 실행

```powershell
cd C:\my\ddl-term-extractor
uv run streamlit run app.py
```

### 가상환경 활성화 후 실행

```powershell
cd C:\my\ddl-term-extractor
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

브라우저에서 **http://localhost:8501** 로 접속합니다.

## 데이터 저장 위치

- SQLite DB 파일: **`data/terms.db`** (최초 실행 시 `data` 폴더가 생성됩니다.)
- WAL 모드 사용 시 같은 폴더에 `-wal` / `-shm` 파일이 생길 수 있습니다.

## 기능 목록

| 구분 | 설명 |
|------|------|
| DDL 입력 | 텍스트 영역에 붙여넣기, 또는 `.sql` / `.txt` / `.ddl` 파일 업로드 |
| PostgreSQL 파싱 | `CREATE TABLE`, `COMMENT ON TABLE` / `COMMENT ON COLUMN`, 컬럼 뒤 인라인 `--` 주석 |
| 용어명 | `COMMENT ON COLUMN` 우선, 없으면 인라인 `--` 주석, 괄호 안 보조 설명은 용어명에서 제거 |
| 용어영문명 | 컬럼명 **소문자 snake_case** |
| 용어정의·도메인명 | 컬럼은 유지, 추출 단계에서는 비움 (DB 재추출 시 빈 값은 기존 DB 값을 덮어쓰지 않음) |
| 인포타입·데이터타입 | PostgreSQL 타입 기준으로 생성·표기 |
| 추출 결과 미리보기 | 테이블로 표시 |
| 이번 추출 Excel | 메인 화면에서 **이번 추출 결과**만 다운로드 |
| SQLite 누적 | 추출 시 **용어영문명** 기준 UPSERT (신규/갱신 건수 표시) |
| DB 현황 | 사이드바에 누적 건수, 용어명 유·무 통계 |
| DB 전체 Excel | 사이드바에서 누적 전체 다운로드 |
| 누적 데이터 초기화 | 사이드바 확장 영역에서 확인 체크 후 **전부 삭제** (되돌리기 불가) |

## DDL 작성 시 참고

- `COMMENT ON COLUMN`이 있으면 용어명에 가장 우선 반영됩니다.
- 인라인 주석만 있는 컬럼은 그 텍스트가 용어명 후보로 사용됩니다.
- 주석이 전혀 없는 컬럼은 용어명이 비어 있을 수 있습니다.
- 여러 테이블에 같은 컬럼명이 있으면 DB에는 **한 건**으로 합쳐집니다.

## 프로젝트 구조 (요약)

```
ddl-term-extractor/
  app.py              # Streamlit UI
  core/
    parser.py         # DDL 파싱
    extractor.py      # 용어 레코드 변환
    excel_writer.py   # Excel 출력
    db.py             # SQLite 저장·조회·초기화
  data/
    terms.db          # 누적 DB (실행 후 생성)
  tests/              # 샘플 SQL 등
```

## 라이선스

프로젝트에 별도 LICENSE 파일이 없다면 내부/개인 용도에 맞게 사용하시면 됩니다.
