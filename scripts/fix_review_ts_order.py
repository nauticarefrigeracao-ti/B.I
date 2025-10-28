#!/usr/bin/env python3
"""
Safe single-order timestamp fixer.

Usage:
  python fix_review_ts_order.py <ORDER_ID> [--apply] [--backup]

What it does:
 - Makes a binary copy backup of ml_devolucoes.db if --backup is given (recommended).
 - Loads the `reviews` row for the provided order_id.
 - If `reviewed_at` is NULL -> reports and exits.
 - If `reviewed_at` already contains a timezone offset (e.g. +00:00 or Z) -> reports and exits.
 - Otherwise (naive timestamp), it will append '+00:00' to make it UTC-aware and UPDATE the row (only if --apply provided).
 - After change, prints the raw and the display-formatted value (using app_streamlit's `_convert_ts_for_display`).

Note: This script modifies the SQLite DB only when --apply is passed. Always run with --backup first and inspect results.
"""

import sqlite3
from pathlib import Path
import shutil
import sys
import re
import argparse
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / 'app_streamlit.py'
if not APP_PATH.exists():
    print(f"app_streamlit.py not found at {APP_PATH}")
    sys.exit(2)
spec = importlib.util.spec_from_file_location('app_streamlit', str(APP_PATH))
app_mod = importlib.util.module_from_spec(spec)
import sys as _sys
_sys.modules['app_streamlit'] = app_mod
spec.loader.exec_module(app_mod)
_convert_ts_for_display = app_mod._convert_ts_for_display
DB_PATH = app_mod.DB_PATH

parser = argparse.ArgumentParser()
parser.add_argument('order_id')
parser.add_argument('--apply', action='store_true', help='Actually perform the DB update. Without this flag the script only reports.')
parser.add_argument('--backup', action='store_true', help='Create a binary backup of the DB before applying changes.')
args = parser.parse_args()

ORDER_ID = args.order_id
MAKE_BACKUP = args.backup
DO_APPLY = args.apply

if not Path(DB_PATH).exists():
    print(f"DB not found at {DB_PATH} — aborting")
    sys.exit(1)

if MAKE_BACKUP:
    bak_name = str(DB_PATH) + '.bak.fix_review_ts_order'
    shutil.copy2(DB_PATH, bak_name)
    print(f"Backup created: {bak_name}")

con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute('SELECT order_id, reviewed, reviewed_by, reviewed_at FROM reviews WHERE order_id = ?', (ORDER_ID,))
row = cur.fetchone()
if not row:
    print(f'No review row found for Order ID {ORDER_ID}')
    con.close()
    sys.exit(0)

raw = row['reviewed_at']
print('Current row:')
print(dict(row))

if raw is None:
    print('reviewed_at is NULL — nothing to do.')
    con.close()
    sys.exit(0)

# detect timezone markers: +HH:MM, +HHMM, Z, or - equivalents
if re.search(r"[+-]\d{2}:?\d{2}$", raw) or raw.endswith('Z'):
    print('Timestamp already timezone-aware. No DB change suggested.')
    # Show display conversion
    df = app_mod.pd.DataFrame([dict(row)])
    df2 = _convert_ts_for_display(df.copy(), ts_cols='reviewed_at')
    print('\nDisplay (America/Sao_Paulo):', df2.loc[0,'reviewed_at'])
    con.close()
    sys.exit(0)

print('Detected naive timestamp (no timezone offset). Suggested fix: append +00:00 to make it UTC-aware.')
print('Raw value:', repr(raw))

if not DO_APPLY:
    print('\nDRY RUN: no change applied. To apply, re-run with --apply --backup')
    # show simulation
    simulated = raw + '+00:00'
    print('Simulated new raw (UTC-aware):', simulated)
    df_sim = app_mod.pd.DataFrame([{'order_id': ORDER_ID, 'reviewed_by': row['reviewed_by'], 'reviewed_at': simulated}])
    df_conv = _convert_ts_for_display(df_sim.copy(), ts_cols='reviewed_at')
    print('Simulated display (America/Sao_Paulo):', df_conv.loc[0,'reviewed_at'])
    con.close()
    sys.exit(0)

# Apply the update
new_raw = raw + '+00:00'
cur.execute("UPDATE reviews SET reviewed_at = ? WHERE order_id = ?", (new_raw, ORDER_ID))
con.commit()
print('Updated DB row — new raw value:', new_raw)
# show converted display
cur.execute('SELECT order_id, reviewed_by, reviewed_at FROM reviews WHERE order_id = ?', (ORDER_ID,))
row2 = cur.fetchone()
df_after = app_mod.pd.DataFrame([dict(row2)])
df_after_conv = _convert_ts_for_display(df_after.copy(), ts_cols='reviewed_at')
print('New display (America/Sao_Paulo):', df_after_conv.loc[0,'reviewed_at'])
con.close()
print('Done.')
