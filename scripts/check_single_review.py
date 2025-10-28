import sqlite3
from pathlib import Path
import pandas as pd
import importlib.util
import sys

if len(sys.argv) < 2:
    print('Usage: python check_single_review.py <ORDER_ID>')
    sys.exit(2)
ORDER_ID = sys.argv[1]

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / 'app_streamlit.py'
if not APP_PATH.exists():
    raise SystemExit(f"app_streamlit.py not found at expected path: {APP_PATH}")
spec = importlib.util.spec_from_file_location('app_streamlit', str(APP_PATH))
app_mod = importlib.util.module_from_spec(spec)
import sys as _sys
_sys.modules['app_streamlit'] = app_mod
spec.loader.exec_module(app_mod)
_convert_ts_for_display = app_mod._convert_ts_for_display
DB_PATH = app_mod.DB_PATH

print('DB path:', DB_PATH)
if not Path(DB_PATH).exists():
    print('DB file not found locally. Aborting check.')
    sys.exit(1)

con = sqlite3.connect(DB_PATH)
try:
    df = pd.read_sql('SELECT order_id, reviewed, reviewed_by, reviewed_at, review_description FROM reviews WHERE order_id = ?', con, params=(ORDER_ID,))
finally:
    con.close()

if df.empty:
    print(f'No review row found for Order ID {ORDER_ID}')
    sys.exit(0)

print('\n=== Raw row ===')
print(df.to_string(index=False))

# convert a copy
df2 = df.copy()
df2 = _convert_ts_for_display(df2, ts_cols='reviewed_at')
print('\n=== Converted for display (America/Sao_Paulo) ===')
print(df2.to_string(index=False))

# show mapping
raw = df.loc[0, 'reviewed_at']
conv = df2.loc[0, 'reviewed_at'] if 'reviewed_at' in df2.columns else ''
print(f"\nMapping: raw={repr(raw)} -> display={repr(conv)}")

# show SQL fix suggestion if naive timestamp detected
import re
if isinstance(raw, str):
    # detect if contains timezone offset like +00:00
    if re.search(r"[+-]\d{2}:?\d{2}$", raw) or raw.endswith('Z'):
        print('\nDetected aware timestamp in DB (has timezone). No DB change suggested.')
    else:
        print('\nDetected naive timestamp in DB (no timezone offset).')
        print('Suggested SQL to convert this single row to UTC-aware (make backup first):')
        print("-- Backup file first:\n-- .backup ml_devolucoes.db.bak_before_normalize.db\n")
        print("UPDATE reviews SET reviewed_at = reviewed_at || '+00:00' WHERE order_id = '" + ORDER_ID + "' AND reviewed_at NOT LIKE '%+%';")

print('\nDone.')
