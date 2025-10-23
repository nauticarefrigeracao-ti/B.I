#!/usr/bin/env python3
"""Gerador de relatórios a partir de ml_devolucoes.db

Gera planilhas Excel com detalhes e resumos (por SKU e por mês) e um CSV
com casos pendentes. É intencionalmente configurável: a lista de colunas
que compõem o valor "passível de extorno" pode ser ajustada.

Uso:
  python reports.py --db ml_devolucoes.db --out reports/prejuizos.xlsx --only-pending

Opções úteis:
  --date-from YYYY-MM-DD --date-to YYYY-MM-DD  (filtrar por data de venda)
  --sku SKU                                     (filtrar por SKU)
  --only-pending                                 (apenas casos com valor pendente)
  --top N                                        (no resumo por SKU, mostrar top N)

Observação: a definição de "valor passível de extorno" é uma heurística
inicial que soma os valores negativos em um conjunto de colunas (por ex.:
cancelamentos, tarifas de envio, tarifa de venda). Ajuste `RECLAIM_COLS`
se necessário e reexecute.
"""

import argparse
from pathlib import Path
import sqlite3
import pandas as pd
import datetime


RECLAIM_COLS = [
    'cancelamentos_reembolsos_brl',
    'tarifas_envio_brl',
    'tarifa_venda_impostos_brl'
]


def load_table(db_path: str):
    con = sqlite3.connect(db_path)
    df = pd.read_sql('select * from devolucoes_clean', con)
    con.close()
    return df


def to_numeric_cols(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
    return df


def compute_reclaim(df):
    # garante colunas numéricas
    df = to_numeric_cols(df, RECLAIM_COLS + ['total_(brl)', 'dinheiro_liberado'])

    # valor passível de extorno = soma dos valores negativos dessas colunas (convertidos para positivo)
    def row_reclaim(r):
        s = 0.0
        for c in RECLAIM_COLS:
            if c in r.index and pd.notna(r[c]):
                val = float(r[c])
                if val < 0:
                    s += -val
        return s

    df['_valor_passivel_extorno'] = df.apply(row_reclaim, axis=1)

    # dinheiro_liberado (o que já foi liberado para o vendedor) usado como proxy de reembolso
    if 'dinheiro_liberado' in df.columns:
        df['dinheiro_liberado'] = pd.to_numeric(df['dinheiro_liberado'], errors='coerce').fillna(0.0)
    else:
        df['dinheiro_liberado'] = 0.0

    # pendente = valor_passivel - dinheiro_liberado (se positivo)
    df['_valor_pendente'] = (df['_valor_passivel_extorno'] - df['dinheiro_liberado']).clip(lower=0.0)

    return df


def filter_df(df, date_from=None, date_to=None, sku=None):
    # filtra por data de venda se a coluna existir
    if date_from is not None and 'data_da_venda' in df.columns:
        df['data_da_venda'] = pd.to_datetime(df['data_da_venda'], dayfirst=True, errors='coerce')
        df = df[df['data_da_venda'] >= pd.to_datetime(date_from)]
    if date_to is not None and 'data_da_venda' in df.columns:
        df = df[df['data_da_venda'] <= pd.to_datetime(date_to)]
    if sku is not None and 'sku' in df.columns:
        df = df[df['sku'].astype(str).str.contains(sku, na=False)]
    return df


def summary_by_sku(df, top=50):
    if 'sku' not in df.columns:
        return pd.DataFrame()
    id_col = 'n_de_venda' if 'n_de_venda' in df.columns else df.columns[0]
    total_col = 'total_brl' if 'total_brl' in df.columns else ('total_(brl)' if 'total_(brl)' in df.columns else None)
    agg_map = {
        'vendas_count': (id_col, 'count'),
        'total_prejuizo': ('_valor_pendente', 'sum')
    }
    if total_col:
        agg_map['total_valor'] = (total_col, 'sum')
    g = df.groupby('sku').agg(**agg_map).sort_values('total_prejuizo', ascending=False).head(top)
    return g.reset_index()


def summary_by_month(df):
    if 'data_da_venda' not in df.columns and 'data_venda' not in df.columns:
        return pd.DataFrame()
    date_col = 'data_da_venda' if 'data_da_venda' in df.columns else 'data_venda'
    # garantir tipo datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    df['mes'] = df[date_col].dt.to_period('M')
    g = df.groupby('mes').agg(
        vendas_count=('n.o_de_venda' if 'n.o_de_venda' in df.columns else df.columns[0], 'count'),
        total_prejuizo=('_valor_pendente', 'sum')
    )
    return g.reset_index()


def generate_reports(db_path, out_path, date_from=None, date_to=None, sku=None, only_pending=False, top=50):
    df = load_table(db_path)
    df = compute_reclaim(df)
    df = filter_df(df, date_from, date_to, sku)

    if only_pending:
        df_out = df[df['_valor_pendente'] > 0].copy()
    else:
        df_out = df.copy()

    # criar pasta de saída
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)

    # resumo por SKU e por mês
    sku_summary = summary_by_sku(df_out, top=top)
    month_summary = summary_by_month(df_out)

    # salva Excel com múltiplas abas
    with pd.ExcelWriter(outp, engine='openpyxl') as w:
        df_out.to_excel(w, sheet_name='detalhes', index=False)
        
        if not sku_summary.empty:
            sku_summary.to_excel(w, sheet_name='resumo_por_sku', index=False)
        if not month_summary.empty:
            month_summary.to_excel(w, sheet_name='resumo_por_mes', index=False)

    # salva CSV separado com casos pendentes
    csv_pending = outp.with_name(outp.stem + '_pendentes.csv')
    df_out[df_out['_valor_pendente'] > 0].to_csv(csv_pending, index=False, encoding='utf-8-sig')

    print('Relatório salvo em:', outp)
    print('CSV pendentes salvo em:', csv_pending)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=False, default='ml_devolucoes.db')
    parser.add_argument('--out', required=False, default='reports/prejuizos.xlsx')
    parser.add_argument('--date-from', required=False)
    parser.add_argument('--date-to', required=False)
    parser.add_argument('--sku', required=False)
    parser.add_argument('--only-pending', action='store_true')
    parser.add_argument('--top', type=int, default=50)
    args = parser.parse_args()

    dbp = args.db
    if not Path(dbp).exists():
        print('Banco não encontrado:', dbp)
        return

    generate_reports(dbp, args.out, args.date_from, args.date_to, args.sku, args.only_pending, args.top)


if __name__ == '__main__':
    main()
