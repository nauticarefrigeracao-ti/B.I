import sqlite3
import pandas as pd
from pathlib import Path

DB = Path('ml_devolucoes.db')
if not DB.exists():
    print('ERROR: database not found at', DB)
    raise SystemExit(1)

con = sqlite3.connect(DB)
q = "SELECT motivo_resultado FROM orders WHERE motivo_resultado IS NOT NULL UNION ALL SELECT motivo_resultado FROM returns WHERE motivo_resultado IS NOT NULL"
try:
    df = pd.read_sql(q, con)
finally:
    con.close()

if df.empty:
    print('NO_MOTIVOS')
else:
    counts = df['motivo_resultado'].astype(str).str.strip().replace('', pd.NA).dropna().value_counts().head(50)
    for motivo, cnt in counts.items():
        print(f"{cnt}\t{motivo}")
