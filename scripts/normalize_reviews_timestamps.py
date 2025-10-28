#!/usr/bin/env python3
"""
Normalize reviews.reviewed_at values in ml_devolucoes.db.

Behavior:
- Create a timestamped backup copy of ml_devolucoes.db in the same folder.
- For each row in reviews where reviewed_at is NOT NULL and parses as a naive datetime
  (no tzinfo), interpret it as America/Sao_Paulo local time, convert to UTC, and
  store back as ISO8601 with +00:00 (e.g. 2025-10-27T19:03:00+00:00).
- Print a short summary with counts and examples.

This is idempotent: running multiple times will only change naive values; aware
values are left untouched.

Run: python scripts/normalize_reviews_timestamps.py
"""
import shutil
import sqlite3
from pathlib import Path
from datetime import timezone
from zoneinfo import ZoneInfo
from dateutil import parser

DB_PATH = Path('ml_devolucoes.db')
BACKUP_FMT = 'ml_devolucoes.db.bak.normalize_{ts}.db'

def backup_db():
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH.resolve()}")
    import datetime
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = DB_PATH.parent / BACKUP_FMT.format(ts=ts)
    shutil.copy2(DB_PATH, dest)
    return dest


def is_naive_timestamp(s: str):
    if s is None:
        return False
    s = str(s).strip()
    if not s:
        return False
    # quick heuristic: presence of Z or +HH or -HH implies aware
    if 'Z' in s or '+' in s or '-' in s[10:]:
        # cautious: strings like 2025-10-27T09:49:31.589199 contain '-' in date part
        # the check above ignores the date-section by slicing after position 10
        try:
            dt = parser.parse(s)
            return dt.tzinfo is None
        except Exception:
            return False
    else:
        # no explicit offset char -> try parse and check tzinfo
        try:
            dt = parser.parse(s)
            return dt.tzinfo is None
        except Exception:
            return False


def normalize():
    backup = backup_db()
    print(f"Backup created at: {backup}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT order_id, reviewed_at FROM reviews WHERE reviewed_at IS NOT NULL")
    rows = cur.fetchall()
    changed = 0
    examples = []
    tz_local = ZoneInfo('America/Sao_Paulo')
    for order_id, reviewed_at in rows:
        s = reviewed_at
        if not is_naive_timestamp(s):
            continue
        try:
            dt = parser.parse(s)
        except Exception:
            continue
        if dt.tzinfo is not None:
            continue
        # localize to Sao_Paulo then convert to UTC
        dt_local = dt.replace(tzinfo=tz_local)
        dt_utc = dt_local.astimezone(timezone.utc)
        new_iso = dt_utc.isoformat()
        # update DB
        cur.execute("UPDATE reviews SET reviewed_at = ? WHERE order_id = ?", (new_iso, order_id))
        changed += 1
        if len(examples) < 10:
            examples.append((order_id, s, new_iso))
    con.commit()
    con.close()
    print(f"Normalized {changed} rows (naive -> UTC ISO).")
    if examples:
        print("Examples (order_id, before, after):")
        for e in examples:
            print(" - ", e)

if __name__ == '__main__':
    normalize()
