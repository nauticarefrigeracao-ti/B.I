import sqlite3
import datetime
from datetime import timezone
con = sqlite3.connect('ml_devolucoes.db')
cur = con.cursor()
cur.execute("REPLACE INTO reviews (order_id, reviewed, reviewed_by, reviewed_at, review_description) VALUES (?,?,?,?,?)",
            ('TEST-TS-1',1,'tester', datetime.datetime.now(tz=timezone.utc).isoformat(), 'test'))
con.commit()
# read back
cur.execute("SELECT order_id, reviewed, reviewed_by, reviewed_at FROM reviews WHERE order_id='TEST-TS-1'")
print(cur.fetchone())
con.close()
# Now format as UI does
import pandas as pd
s = pd.Series(['2025-10-27T12:00:00+00:00', None, '2025-10-27T06:00:00'])
print('raw:', s.tolist())
try:
    parsed = pd.to_datetime(s, utc=True, errors='coerce').dt.tz_convert('America/Sao_Paulo').dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
    print('parsed:', parsed.tolist())
except Exception as e:
    print('parse error', e)
