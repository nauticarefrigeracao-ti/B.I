# Análise de Devoluções - Progresso

Conteúdo deste pacote:

- `analisar_devolucoes.py` : script principal usado para identificar devoluções e valores pendentes.
- `table.xlsx` : amostra (o arquivo que você forneceu) — usado para validação.
- `pendentes.csv`, `prejuizos.csv` : saídas geradas pelo script.
- `etl_to_sqlite.py` : script para agregar múltiplos CSVs em um banco SQLite (base para análises).
- `requirements.txt` : dependências recomendadas.

Objetivo imediato:

1. Consolidar até ~6 meses de CSVs (exportados do Mercado Livre) em uma base SQLite.
2. Normalizar colunas (nomes, tipos, valores monetários) e adicionar metadados (mês, origem do arquivo).
3. Gerar consultas e dashboards (Streamlit / Plotly) para identificar padrões, montantes a contestar e performance.

Como usar:

1. Instale dependências:

```pwsh
pip install -r requirements.txt
```

2. Copie seus CSVs para uma pasta, por exemplo `C:\Users\Pichau\csvs`.

3. Rode o ETL para consolidar:

```pwsh
python etl_to_sqlite.py --input-dir C:\Users\Pichau\csvs --db C:\Users\Pichau\analise_progress\ml_devolucoes.db
```

4. Abra o banco SQLite com `sqlite-utils` ou conecte com ferramentas (DB Browser for SQLite) ou crie dashboards.

Próximos passos (recomendados):
- Definir as métricas chave (totais por mês, prejuízos por SKU, tempo para reembolso, motivos mais comuns).
- Criar dashboards em Streamlit com filtros por período, SKU, motivo e estado.
- Automatizar ingestão (agendar ETL semanalmente) e armazenar históricos.
