import sqlite3
from pathlib import Path
DB = Path('ml_devolucoes.db')
if not DB.exists():
    print('DB not found:', DB)
    raise SystemExit(1)
con = sqlite3.connect(DB)
cur = con.cursor()
print('--- last 30 reviews (order_id, reviewed, reviewed_by, reviewed_at_repr, review_description) ---')
for row in cur.execute("SELECT order_id, reviewed, reviewed_by, reviewed_at, review_description FROM reviews ORDER BY rowid DESC LIMIT 30"):
    # print repr for clarity on timezone markers
    print(repr(row))

print('\n--- last 30 actions (id, order_id, user, action, note, created_at) ---')
try:
    cols = [r[1] for r in cur.execute("PRAGMA table_info(actions)")]
    if cols:
        q = 'SELECT ' + ','.join(cols) + ' FROM actions ORDER BY ROWID DESC LIMIT 30'
        for row in cur.execute(q):
            print(repr(row))
    else:
        print('No actions table present or empty schema')
except Exception as e:
    print('Failed to read actions table:', repr(e))
con.close()
