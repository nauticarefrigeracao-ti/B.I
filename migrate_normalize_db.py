#!/usr/bin/env python3
"""Migração e normalização do banco ml_devolucoes.db

Cria tabelas: orders, order_items, buyers, shipments, returns, complaints, fees, actions
Cria view: view_orders_financials
Gera relatório top 50 pendências em Excel
"""
import sqlite3
import pandas as pd
from pathlib import Path

DB = Path('ml_devolucoes.db')
OUT_DIR = Path('reports')
OUT_DIR.mkdir(exist_ok=True)

RECLAIM_COLS = ['cancelamentos_reembolsos_brl', 'tarifas_envio_brl', 'tarifa_venda_impostos_brl']


def to_num(s):
    try:
        return float(s)
    except Exception:
        return 0.0


def main():
    if not DB.exists():
        print('Banco não encontrado:', DB)
        return

    con = sqlite3.connect(str(DB))
    df = pd.read_sql('select * from devolucoes_clean', con)
    print('Linhas originais:', len(df))

    # Normalizar nomes de colunas (já estão em snake_case na tabela)

    # Garantir colunas numéricas
    num_cols = ['total_brl', 'receita_por_produtos_brl', 'receita_por_envio_brl',
                'tarifas_envio_brl', 'tarifa_venda_impostos_brl', 'cancelamentos_reembolsos_brl',
                'preco_unitario_brl', 'dinheiro_liberado']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
        else:
            df[c] = 0.0

    # datas
    for c in df.columns:
        if 'data' in c:
            try:
                df[c] = pd.to_datetime(df[c], dayfirst=True, errors='coerce')
            except Exception:
                pass

    # indicadores financeiros
    def row_reclaim(r):
        s = 0.0
        for c in RECLAIM_COLS:
            if c in r.index and pd.notna(r[c]):
                val = to_num(r[c])
                if val < 0:
                    s += -val
        return s

    df['_valor_passivel_extorno'] = df.apply(row_reclaim, axis=1)
    df['_valor_pendente'] = (df['_valor_passivel_extorno'] - df['dinheiro_liberado']).clip(lower=0.0)

    # criar tabelas normalizadas
    cur = con.cursor()

    # drop se existirem (safe for reruns)
    cur.executescript('''
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS buyers;
    DROP TABLE IF EXISTS shipments;
    DROP TABLE IF EXISTS returns;
    DROP TABLE IF EXISTS complaints;
    DROP TABLE IF EXISTS fees;
    DROP TABLE IF EXISTS actions;
    DROP VIEW IF EXISTS view_orders_financials;
    ''')

    cur.executescript('''
    CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        data_venda TIMESTAMP,
        estado TEXT,
        descricao_status TEXT,
        total_brl NUMERIC,
        receita_produtos_brl NUMERIC,
        receita_envio_brl NUMERIC,
        tarifa_venda_impostos_brl NUMERIC,
        tarifas_envio_brl NUMERIC,
        cancelamentos_reembolsos_brl NUMERIC,
        dinheiro_liberado NUMERIC,
        resultado TEXT,
        motivo_resultado TEXT,
        mes_faturamento TEXT,
        source_file TEXT,
        _valor_passivel_extorno NUMERIC,
        _valor_pendente NUMERIC
    );

    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        sku TEXT,
        anuncio_id TEXT,
        titulo TEXT,
        variacao TEXT,
        preco_unitario NUMERIC,
        unidades INTEGER
    );

    CREATE TABLE buyers (
        buyer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        comprador TEXT,
        cpf TEXT,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        pais TEXT
    );

    CREATE TABLE shipments (
        shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        forma_de_entrega TEXT,
        data_a_caminho TIMESTAMP,
        data_de_entrega TIMESTAMP,
        motorista TEXT,
        numero_de_rastreamento TEXT,
        url_acompanhamento TEXT
    );

    CREATE TABLE returns (
        return_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        revisado_pelo_mercado_livre TEXT,
        data_de_revisao TIMESTAMP,
        dinheiro_liberado NUMERIC,
        resultado TEXT,
        destino TEXT,
        motivo_resultado TEXT
    );

    CREATE TABLE complaints (
        complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        unidades INTEGER,
        reclamacao_aberta TEXT,
        reclamacao_encerrada TEXT,
        em_mediacao TEXT
    );

    CREATE TABLE fees (
        fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        fee_type TEXT,
        amount NUMERIC
    );

    CREATE TABLE actions (
        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        user TEXT,
        action TEXT,
        note TEXT,
        ts TIMESTAMP DEFAULT (datetime('now'))
    );
    ''')
    con.commit()

    # popular buyers (unique by comprador + cpf)
    buyers = {}
    for idx, r in df.iterrows():
        key = (str(r.get('comprador', '')), str(r.get('cpf', '')))
        if key not in buyers:
            buyers[key] = (r.get('comprador'), r.get('cpf'), r.get('endereco.1') if 'endereco.1' in df.columns else r.get('endereco'), r.get('cidade'), r.get('estado.1') if 'estado.1' in df.columns else r.get('estado'), r.get('cep'), r.get('pais'))
    for v in buyers.values():
        cur.execute('INSERT INTO buyers (comprador, cpf, endereco, cidade, estado, cep, pais) VALUES (?,?,?,?,?,?,?)', v)
    con.commit()

    # popular orders, items, shipments, returns, complaints
    for idx, r in df.iterrows():
        order_id = str(r.get('n_de_venda'))
        if not order_id:
            continue
        data_venda = r.get('data_venda')
        if hasattr(data_venda, 'isoformat'):
            data_venda_val = data_venda.isoformat()
        else:
            data_venda_val = None if pd.isna(data_venda) else str(data_venda)

        cur.execute('INSERT OR REPLACE INTO orders (order_id, data_venda, estado, descricao_status, total_brl, receita_produtos_brl, receita_envio_brl, tarifa_venda_impostos_brl, tarifas_envio_brl, cancelamentos_reembolsos_brl, dinheiro_liberado, resultado, motivo_resultado, mes_faturamento, source_file, _valor_passivel_extorno, _valor_pendente) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            order_id,
            data_venda_val,
            r.get('estado'),
            r.get('descricao_do_status'),
            r.get('total_brl'),
            r.get('receita_por_produtos_brl'),
            r.get('receita_por_envio_brl'),
            r.get('tarifa_venda_impostos_brl'),
            r.get('tarifas_envio_brl'),
            r.get('cancelamentos_reembolsos_brl'),
            r.get('dinheiro_liberado'),
            r.get('resultado'),
            r.get('motivo_resultado'),
            r.get('mes_de_faturamento_das_suas_tarifas'),
            r.get('_source_file'),
            r.get('_valor_passivel_extorno'),
            r.get('_valor_pendente')
        ))

        # items
        sku = r.get('sku')
        anuncio = r.get('anuncio_id') if 'anuncio_id' in r else r.get('# de anúncio')
        titulo = r.get('titulo_do_anuncio')
        variacao = r.get('variacao')
        preco = r.get('preco_unitario_brl') if 'preco_unitario_brl' in r else 0.0
        def parse_unidades(val):
            try:
                if pd.isna(val):
                    return 1
                s = str(val).strip()
                if s == '':
                    return 1
                return int(float(s))
            except Exception:
                return 1
        unidades = parse_unidades(r.get('unidades') if r.get('unidades') not in (None, '') else (r.get('unidades.1') if 'unidades.1' in r else 1))
        cur.execute('INSERT INTO order_items (order_id, sku, anuncio_id, titulo, variacao, preco_unitario, unidades) VALUES (?,?,?,?,?,?,?)', (order_id, sku, anuncio, titulo, variacao, preco, unidades))

        # shipments (principal)
        dac = r.get('data_a_caminho')
        dde = r.get('data_de_entrega')
        if hasattr(dac, 'isoformat'):
            dac_v = dac.isoformat()
        else:
            dac_v = None if pd.isna(dac) else str(dac)
        if hasattr(dde, 'isoformat'):
            dde_v = dde.isoformat()
        else:
            dde_v = None if pd.isna(dde) else str(dde)

        cur.execute('INSERT INTO shipments (order_id, forma_de_entrega, data_a_caminho, data_de_entrega, motorista, numero_de_rastreamento, url_acompanhamento) VALUES (?,?,?,?,?,?,?)', (
            order_id,
            r.get('forma_de_entrega'),
            dac_v,
            dde_v,
            r.get('motorista'),
            r.get('numero_de_rastreamento'),
            r.get('url_acompanhamento')
        ))

        # returns
        ddr = r.get('data_de_revisao')
        if hasattr(ddr, 'isoformat'):
            ddr_v = ddr.isoformat()
        else:
            ddr_v = None if pd.isna(ddr) else str(ddr)

        cur.execute('INSERT INTO returns (order_id, revisado_pelo_mercado_livre, data_de_revisao, dinheiro_liberado, resultado, destino, motivo_resultado) VALUES (?,?,?,?,?,?,?)', (
            order_id,
            r.get('revisado_pelo_mercado_livre'),
            ddr_v,
            r.get('dinheiro_liberado'),
            r.get('resultado'),
            r.get('destino'),
            r.get('motivo_resultado')
        ))

        # complaints
        cur.execute('INSERT INTO complaints (order_id, unidades, reclamacao_aberta, reclamacao_encerrada, em_mediacao) VALUES (?,?,?,?,?)', (
            order_id,
            r.get('unidades.2') if 'unidades.2' in r else r.get('unidades'),
            r.get('reclamacao_aberta'),
            r.get('reclamacao_encerrada'),
            r.get('em_mediacao')
        ))

        # fees: gravar linhas se existirem valores não-zero
        for fee_name in ['tarifa_venda_impostos_brl', 'tarifas_envio_brl', 'cancelamentos_reembolsos_brl']:
            if fee_name in r and r.get(fee_name) not in (None, 0, 0.0, '0'):
                cur.execute('INSERT INTO fees (order_id, fee_type, amount) VALUES (?,?,?)', (order_id, fee_name, r.get(fee_name)))

    con.commit()

    # criar view financeira
    cur.executescript('''
    CREATE VIEW view_orders_financials AS
    SELECT
      o.order_id,
      o.data_venda,
      o.total_brl,
      o.receita_produtos_brl,
      o.receita_envio_brl,
      o.tarifa_venda_impostos_brl,
      o.tarifas_envio_brl,
      o.cancelamentos_reembolsos_brl,
      o.dinheiro_liberado,
      o._valor_passivel_extorno,
      o._valor_pendente
    FROM orders o;
    ''')
    con.commit()

    # relatório top50 pendências por SKU
    q = '''SELECT oi.sku, sum(o._valor_pendente) as prejuizo, count(*) as vendas
           FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
           WHERE o._valor_pendente > 0
           GROUP BY oi.sku
           ORDER BY prejuizo DESC
           LIMIT 50'''
    top50 = pd.read_sql(q, con)
    top50.to_excel(OUT_DIR / '50_mais_pendentes.xlsx', index=False)

    # relatório detalhado top 50 ordens (ordenado)
    q2 = '''SELECT o.order_id, o.data_venda, oi.sku, oi.preco_unitario, oi.unidades, o._valor_passivel_extorno, o._valor_pendente, o.dinheiro_liberado, o.total_brl, o.resultado
            FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o._valor_pendente > 0
            ORDER BY o._valor_pendente DESC
            LIMIT 100'''
    det = pd.read_sql(q2, con)
    det.to_excel(OUT_DIR / '100_mais_pendentes_detalhado.xlsx', index=False)

    print('Migração concluída. Tabelas criadas e relatórios gerados em', OUT_DIR)
    con.close()

if __name__ == '__main__':
    main()
