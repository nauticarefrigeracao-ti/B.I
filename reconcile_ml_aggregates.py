from pathlib import Path
import sqlite3
import pandas as pd
import csv
import sys

ML_CSV = Path(r"C:\Users\Pichau\Downloads\Planilha sem título - Negócio.csv")
DB = Path(r"c:\Users\Pichau\analise_progress\ml_devolucoes.db")
OUT = Path("reports")
OUT.mkdir(exist_ok=True)
OUT_FILE = OUT / "ml_reconciliation_2025-09.csv"

if not ML_CSV.exists():
    print(f"ML CSV not found at {ML_CSV}. Please place the Mercado Livre export in that path.")
    sys.exit(1)
if not DB.exists():
    print(f"Database not found at {DB}")
    sys.exit(1)

def find_header_row(path):
    # find the row index where header starts (first column 'Data' expected)
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if line.strip().startswith('Data,') or line.strip().split(',')[0].strip() == 'Data':
                return i
    return None

hdr_row = find_header_row(ML_CSV)
if hdr_row is None:
    print('Could not find header row in ML CSV; open the file and confirm it contains the expected header starting with "Data"')
    sys.exit(1)

# read with pandas using located header row
df_ml = pd.read_csv(ML_CSV, header=hdr_row, skip_blank_lines=True, encoding='utf-8', dtype=str)

def to_number(s):
    if pd.isna(s):
        return 0.0
    s = str(s).strip()
    if s == '':
        return 0.0
    # remove percent
    if s.endswith('%'):
        try:
            return float(s.replace('%','').replace(',','.'))/100.0
        except:
            return 0.0
    # normalize thousands/decimals: assume pt-BR style '.' thousands and ',' decimals
    s2 = s.replace('.', '').replace(',', '.')
    # remove currency R$
    s2 = s2.replace('R$', '').replace('\xa0','').strip()
    try:
        return float(s2)
    except:
        return 0.0

# relevant ML columns (as in the provided CSV)
ml_cols_map = {
    'vendas_brutas':'Vendas brutas',
    'quantidade_vendas':'Quantidade de vendas',
    'unidades_vendidas':'Unidades vendidas',
    'quantidade_vendas_canceladas':'Quantidade de vendas canceladas',
    'valor_vendas_canceladas':'Valor de vendas canceladas',
    'quantidade_vendas_devolvidas':'Quantidade de vendas devolvidas',
    'valor_vendas_devolvidas':'Valor de vendas devolvidas'
}

ml_aggr = {}
for k, col in ml_cols_map.items():
    if col in df_ml.columns:
        ml_aggr[k] = df_ml[col].apply(to_number).sum()
    else:
        ml_aggr[k] = 0.0

# compute our DB aggregates for 2025-09-01..2025-09-30
con = sqlite3.connect(str(DB))
q = """
SELECT
  COUNT(DISTINCT o.order_id) AS pedidos,
  SUM(COALESCE(o.total_brl,0)) AS vendas_brutas,
  SUM(COALESCE(oi.unidades,0)) AS unidades_vendidas,
  SUM(COALESCE(o.cancelamentos_reembolsos_brl,0)) AS valor_vendas_canceladas,
  SUM(CASE WHEN lower(o.estado) LIKE '%cancel%' OR lower(o.descricao_status) LIKE '%cancel%' THEN 1 ELSE 0 END) AS quantidade_vendas_canceladas,
  SUM(COALESCE(o._valor_pendente,0)) AS prejuizo_pendente,
  SUM(COALESCE(o.tarifa_venda_impostos_brl,0) + COALESCE(o.tarifas_envio_brl,0)) AS tarifas_totais
FROM orders o
LEFT JOIN order_items oi ON oi.order_id = o.order_id
WHERE date(substr(o.data_venda,1,10)) BETWEEN '2025-09-01' AND '2025-09-30'
"""
df_db = pd.read_sql_query(q, con)
db = df_db.iloc[0].to_dict()

results = []

def pct_diff(local, ml):
    try:
        if ml == 0:
            return None
        return (local - ml) / abs(ml) * 100.0
    except:
        return None

# map DB -> ML keys
rows = [
    ('Vendas brutas', db.get('vendas_brutas',0.0), ml_aggr.get('vendas_brutas',0.0)),
    ('Quantidade de vendas', db.get('pedidos',0.0), ml_aggr.get('quantidade_vendas',0.0)),
    ('Unidades vendidas', db.get('unidades_vendidas',0.0), ml_aggr.get('unidades_vendidas',0.0)),
    ('Quantidade de vendas canceladas', db.get('quantidade_vendas_canceladas',0.0), ml_aggr.get('quantidade_vendas_canceladas',0.0)),
    ('Valor de vendas canceladas', db.get('valor_vendas_canceladas',0.0), ml_aggr.get('valor_vendas_canceladas',0.0)),
    ('Quantidade de vendas devolvidas (heur)', 0.0, ml_aggr.get('quantidade_vendas_devolvidas',0.0)),
    ('Valor de vendas devolvidas (heur)', 0.0, ml_aggr.get('valor_vendas_devolvidas',0.0)),
    ('Prejuízo pendente (nosso)', db.get('_valor_pendente',0.0), None),
    ('Tarifas (nosso sum)', db.get('tarifas_totais',0.0), None)
]

for label, local_val, ml_val in rows:
    diff = None if ml_val is None else (local_val - ml_val)
    pct = None if ml_val is None or ml_val == 0 else (diff / abs(ml_val) * 100.0)
    results.append({
        'metric': label,
        'local': local_val,
        'ml': ml_val,
        'diff': diff,
        'pct_diff': pct
    })

out_df = pd.DataFrame(results)
out_df.to_csv(OUT_FILE, index=False, float_format='%.2f')

print('\nReconciliation summary (2025-09-01 .. 2025-09-30)')
print(out_df.to_string(index=False))
print(f"\nReport written to {OUT_FILE}\n")

con.close()
