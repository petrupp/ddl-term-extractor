"""UPSERT 중복 제거 테스트"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from core.parser import parse_ddl
from core.extractor import tables_to_records
from core.db import upsert_records, fetch_all, get_stats, _DB_PATH

# 테스트용 DB 초기화 (기존 데이터 제거)
if _DB_PATH.exists():
    _DB_PATH.unlink()

base = Path(__file__).parent

with open(base / "sample2.sql", encoding="utf-8") as f:
    ddl = f.read()

# 1차 입력
records = tables_to_records(parse_ddl(ddl))
ins, upd = upsert_records(records)
print(f"[1차] 입력 {len(records)}건 -> 신규 {ins}, 갱신 {upd}")
print(f"  DB 현황: {get_stats()}")

# 2차 동일 입력 (전부 중복)
ins2, upd2 = upsert_records(records)
print(f"[2차] 동일 입력 -> 신규 {ins2}, 갱신 {upd2}")
print(f"  DB 현황: {get_stats()}")

# 3차 sample.sql (created_at 등 중복 컬럼 포함)
with open(base / "sample.sql", encoding="utf-8") as f:
    ddl2 = f.read()
records2 = tables_to_records(parse_ddl(ddl2))
ins3, upd3 = upsert_records(records2)
print(f"[3차] sample.sql {len(records2)}건 -> 신규 {ins3}, 갱신 {upd3}")
print(f"  DB 현황: {get_stats()}")

# 전체 조회
all_rows = fetch_all()
print(f"\n=== DB 전체 {len(all_rows)}건 ===")
for r in all_rows:
    eng = r["용어영문명"]
    name = r["용어명"]
    dtype = r["데이터타입"]
    print(f"  {eng:20s} | {name:12s} | {dtype}")
