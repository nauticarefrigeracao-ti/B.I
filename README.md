# Análise de Devoluções - Progresso

Conteúdo deste pacote:


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

Descrição rápida e deploy
------------------------

Este repositório contém um protótipo Streamlit para análise de devoluções. O arquivo principal da aplicação é `app_streamlit.py` na raiz do repositório.

Execução local (recomendado):

1. Crie e ative um ambiente virtual:

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Rode o Streamlit localmente:

```pwsh
python -m streamlit run .\app_streamlit.py --server.address 127.0.0.1 --server.port 8501
```

Notas para deploy no Streamlit Cloud:

- Na hora de criar a app no Streamlit Cloud, aponte o "Main file path" para `app_streamlit.py` (ou crie um wrapper `streamlit_app.py` que chame `app_streamlit.main()`).
- Se o repositório for privado, autorize o Streamlit Cloud a acessar o GitHub ou torne o repositório público.
- Remova ou migre o arquivo local de banco de dados `ml_devolucoes.db` para um serviço gerenciado (por exemplo Supabase/Postgres) antes do deploy público — o repositório já contém `.gitignore` para evitar enviar esse arquivo.

Quer que eu adicione um `streamlit_app.py` wrapper e um README mais detalhado com passos de migração do DB para Supabase? Posso criar e enviar o commit agora.
