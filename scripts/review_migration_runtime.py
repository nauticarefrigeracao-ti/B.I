import os, sqlite3, shutil, time
from datetime import datetime, timezone
ROOT = os.path.abspath('.')
DB = os.path.join(ROOT, 'ml_devolucoes.db')
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)
bak = DB + '.bak_' + time.strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB, bak)
print('Backup created:', bak)
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
if not cur.fetchone():
    print('No reviews table found, nothing to do.')
    con.close()
    raise SystemExit(0)
cur.execute('PRAGMA table_info(reviews)')
cols = [r[1] for r in cur.fetchall()]
if 'reviewed_at_utc' not in cols:
    cur.execute('ALTER TABLE reviews ADD COLUMN reviewed_at_utc TEXT')
    print('Added column reviewed_at_utc')
else:
    print('Column reviewed_at_utc already exists')

def normalize_to_utc(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        try:
            ts = float(s)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

cur.execute('SELECT order_id, reviewed_at FROM reviews')
rows = cur.fetchall()
updated = 0
for order_id, raw in rows:
    norm = normalize_to_utc(raw)
    if norm:
        cur.execute('UPDATE reviews SET reviewed_at_utc = ? WHERE order_id = ?', (norm, order_id))
        updated += 1

con.commit()
con.close()
print(f'Updated {updated} rows (reviewed_at_utc)')
print('Done. Backup is at:', bak)
