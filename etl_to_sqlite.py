"""ETL simples: agrega vários CSVs/planilhas exportadas do Mercado Livre
e grava em um banco SQLite para análises.

Uso:
  python etl_to_sqlite.py --input-dir C:\caminho\para\csvs --db ml_devolucoes.db

O script tenta normalizar nomes de colunas e tipos básicos.
"""

import argparse
import json
import os
import pandas as pd
import sqlite3
from pathlib import Path


def normalize_columns(df):
    # padrão: lowercase, remove acentos simples, replace spaces
    cols = []
    for c in df.columns:
        s = str(c).lower()
        # remoção simples de acentos (cobertura mínima sem dependências externas)
        s = s.replace("ç", "c").replace("ã", "a").replace("â", "a").replace("á", "a").replace("à", "a").replace("é", "e").replace("ê", "e").replace("í", "i").replace("ó", "o").replace("ô", "o").replace("ú", "u").replace("ü", "u").replace("ñ", "n")
        s = s.replace("º", "o").replace("#", "num").replace("%", "pct")
        s = s.replace(" ", "_").replace("/", "_").replace("\\", "_").replace('"', "_")
        cols.append(s)
    df.columns = cols
    return df


def limpar_valor(valor):
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor)
    # remove espaços e símbolos comuns
    s = s.replace("R$", "").replace("$", "").replace(" ", "")
    # tratar parênteses como negativo
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    # remover pontos de milhar e normalizar vírgula decimal
    s = s.replace(".", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def process_file(path, conn=None, table_name="devolucoes"):
    # agora a função apenas retorna o DataFrame processado; a gravação
    # agregada será feita no final para evitar conflitos de schema entre arquivos.
    print(f"Processando: {path}")
    ext = Path(path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=object)
    else:
        # CSVs exportados pelo Mercado Livre frequentemente têm linhas de cabeçalho
        # extras antes da linha real com nomes das colunas. Detectamos a linha
        # que contém o cabeçalho (procura por "n." ou "n.º de venda") e usamos
        # esse índice como header. Também tentamos alguns encodings comuns.
        header_row = 0
        encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        df = None
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc, errors='replace') as f:
                    sample_lines = [next(f) for _ in range(20)]
                found = None
                for i, L in enumerate(sample_lines):
                    low = L.lower()
                    if ('n.' in low and 'venda' in low) or ('n.º de venda' in low) or ('n. de venda' in low) or ('nº de venda' in low):
                        found = i
                        break
                if found is not None:
                    header_row = found
                df = pd.read_csv(path, dtype=object, header=header_row, encoding=enc)
                break
            except StopIteration:
                # arquivo com poucas linhas
                continue
            except Exception:
                continue
        if df is None:
            # fallback
            df = pd.read_csv(path, dtype=object, encoding='latin-1')

    df = normalize_columns(df)

    # tentar detectar colunas monetárias e normalizar
    money_keys = [c for c in df.columns if any(x in c for x in ["valor", "preco", "preco_unitario", "total", "tarifa", "taxa", "frete", "cancelamento", "reembolso"]) ]
    for c in money_keys:
        df[c] = df[c].apply(limpar_valor)

    # tenta converter colunas de data se existirem
    date_keys = [c for c in df.columns if any(x in c for x in ["data", "date"]) ]
    for c in date_keys:
        try:
            df[c] = pd.to_datetime(df[c], dayfirst=True, errors='coerce')
        except Exception:
            pass

    # adiciona coluna de origem
    df["_source_file"] = os.path.basename(path)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--map", required=False, help="path para columns_map.json")
    parser.add_argument("--out-csv", required=False, help="path para consolidado.csv")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    # load mapping if provided
    mapping = None
    if args.map:
        with open(args.map, "r", encoding="utf-8") as f:
            mapping = json.load(f).get("mappings", {})

    all_dfs = []
    for file in sorted(input_dir.glob("*")):
        if file.suffix.lower() in (".csv", ".xlsx", ".xls"):
            try:
                df = process_file(file, conn)
                all_dfs.append(df)
            except Exception as e:
                print(f"Erro processando {file}: {e}")

    # cria consolidado
    if all_dfs:
        consolidado = pd.concat(all_dfs, ignore_index=True)

        # aplica mapeamento heurístico para esquema limpo
        if mapping:
            new_cols = {}
            lower_cols = {c: c for c in consolidado.columns}
            for std_name, candidates in mapping.items():
                found = None
                for cand in candidates:
                    for col in consolidado.columns:
                        if cand.lower() == col.lower():
                            found = col
                            break
                    if found:
                        break
                if found:
                    new_cols[found] = std_name
            consolidado = consolidado.rename(columns=new_cols)

        # salva consolidado em CSV se solicitado
        if args.out_csv:
            consolidado.to_csv(args.out_csv, index=False, encoding="utf-8-sig")

        # grava tabela limpa no sqlite
        consolidado.to_sql("devolucoes_clean", conn, if_exists="replace", index=False)

    conn.close()
    print("Concluído. Base gerada em:", db_path)


if __name__ == "__main__":
    main()
