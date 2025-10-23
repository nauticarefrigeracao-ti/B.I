from pathlib import Path
import sqlite3
import pandas as pd
import sys

DB = Path("ml_devolucoes.db")
if not DB.exists():
    print("Database ml_devolucoes.db not found in current folder.")
    sys.exit(1)

con = sqlite3.connect(str(DB))

def table_exists(name):
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

tbl = 'devolucoes_clean' if table_exists('devolucoes_clean') else 'orders'

print(f"Using table: {tbl}\n")

month = '2025-09'
q_metrics = f"""
SELECT
  COUNT(DISTINCT order_id) AS pedidos,
  SUM(total_brl) AS vendas_brutas,
  SUM(IFNULL(unidades,0)) AS unidades_vendidas,
  SUM(IFNULL(valor_vendas_canceladas_brl,0)) AS valor_vendas_canceladas,
  SUM(IFNULL(valor_vendas_devolvidas_brl,0)) AS valor_vendas_devolvidas,
  SUM(IFNULL(quantidade_vendas_canceladas,0)) AS quantidade_vendas_canceladas,
  SUM(IFNULL(quantidade_vendas_devolvidas,0)) AS quantidade_vendas_devolvidas,
  SUM(IFNULL(_valor_pendente,0)) AS prejuizo_pendente
FROM {tbl}
WHERE mes_faturamento = ?
"""

try:
    df_metrics = pd.read_sql_query(q_metrics, con, params=(month,))
except Exception:
    # fallback for different column names: try fewer columns
    q_metrics2 = f"""
    SELECT
      COUNT(DISTINCT order_id) AS pedidos,
      SUM(total_brl) AS vendas_brutas,
      SUM(IFNULL(unidades,0)) AS unidades_vendidas,
      SUM(IFNULL(_valor_pendente,0)) AS prejuizo_pendente
    FROM {tbl}
    WHERE mes_faturamento = ?
    """
    df_metrics = pd.read_sql_query(q_metrics2, con, params=(month,))

print(f"Métricas extraídas para {month}:\n")
print(df_metrics.T)

q_sample = f"""
SELECT order_id, data_venda, total_brl, _valor_passivel_extorno, dinheiro_liberado, _valor_pendente, sku, preco_unitario, unidades
FROM {tbl}
WHERE mes_faturamento = ?
ORDER BY data_venda DESC
LIMIT 20
"""

df_sample = pd.read_sql_query(q_sample, con, params=(month,))
print('\nAmostra de pedidos (20):')
print(df_sample.to_string(index=False))

con.close()
