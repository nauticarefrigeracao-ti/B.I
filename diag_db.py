import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path('ml_devolucoes.db')
BAKS = [p for p in Path('.').glob('ml_devolucoes.db.bak_*')]

files = [('current', DB)] + [('bak', p) for p in sorted(BAKS)]

def rows_for(p):
    con = sqlite3.connect(str(p))
    cur = con.cursor()
    try:
        cur.execute("SELECT order_id, reviewed, reviewed_by, reviewed_at FROM reviews ORDER BY ROWID DESC")
        rows = cur.fetchall()
    except Exception as e:
        rows = []
    try:
        cur.execute("SELECT id, order_id, user, action, note, created_at FROM actions ORDER BY id DESC LIMIT 50")
        actions = cur.fetchall()
    except Exception:
        actions = []
    con.close()
    return rows, actions

all_sets = {}
for tag, p in files:
    print('\nFILE:', p, 'exists=', p.exists(), 'size=', p.stat().st_size if p.exists() else 'NA')
    if not p.exists():
        continue
    rows, actions = rows_for(p)
    print('  reviews count:', len(rows))
    # print last 20 reviews
    for r in rows[:20]:
        print('   REV:', r)
    print('  actions count sample:', len(actions))
    for a in actions[:10]:
        print('   ACT:', a)
    all_sets[str(p)] = set([r[0] for r in rows])

# Compare sets: which order_ids are in any backup but not in current
cur_set = all_sets.get(str(DB), set())
others = {k:v for k,v in all_sets.items() if k!=str(DB)}

missing = {}
for k,s in others.items():
    diff = s - cur_set
    if diff:
        missing[k] = diff

print('\nSummary of order_ids present in backups but NOT in current DB:')
for k,d in missing.items():
    print(k, 'missing_count=', len(d))
    sample = list(d)[:20]
    print(' sample missing ids:', sample)

# Also check if there are reviews in current with timestamps that look like UTC vs BR
print('\nChecking timestamp examples (current DB):')
if DB.exists():
    rows, _ = rows_for(DB)
    for r in rows[:40]:
        oid, reviewed, by, at = r
        print(' ', oid, reviewed, by, at)
        # try parse
        try:
            dt = datetime.fromisoformat(at) if at else None
            if dt:
                print('    parsed local:', dt.isoformat())
        except Exception:
            pass

print('\nDiag complete')
