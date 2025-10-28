import sqlite3
from pathlib import Path
import pandas as pd
import importlib.util
import sys

# Import app_streamlit.py by path so this script works regardless of PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / 'app_streamlit.py'
if not APP_PATH.exists():
    raise SystemExit(f"app_streamlit.py not found at expected path: {APP_PATH}")
spec = importlib.util.spec_from_file_location('app_streamlit', str(APP_PATH))
app_mod = importlib.util.module_from_spec(spec)
sys.modules['app_streamlit'] = app_mod
spec.loader.exec_module(app_mod)
_convert_ts_for_display = app_mod._convert_ts_for_display
DB_PATH = app_mod.DB_PATH

def main():
    print('DB path:', DB_PATH)
    if not Path(DB_PATH).exists():
        print('DB file not found locally. Aborting check.')
        return
    con = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql('SELECT order_id, reviewed_by, reviewed_at FROM reviews ORDER BY rowid DESC LIMIT 50', con)
    except Exception as e:
        print('Failed to read reviews table:', e)
        return
    finally:
        con.close()

    if df.empty:
        print('No reviews found in DB.')
        return

    print('\n=== Raw values (first rows) ===')
    print(df.head(10).to_string(index=False))

    # copy and run conversion
    df2 = df.copy()
    df2 = _convert_ts_for_display(df2, ts_cols='reviewed_at')

    print('\n=== Converted for display (America/Sao_Paulo) ===')
    print(df2.head(10).to_string(index=False))

    # show examples where original was naive vs aware
    print('\n=== Examples where original parsing differs (naive vs aware) ===')
    for i, row in df.iterrows():
        orig = row['reviewed_at']
        conv = df2.loc[i, 'reviewed_at'] if 'reviewed_at' in df2.columns else ''
        print(f"{row['order_id']}: orig={repr(orig)} -> display={repr(conv)}")

if __name__ == '__main__':
    main()
