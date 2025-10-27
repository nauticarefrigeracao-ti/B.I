2025-10-27T10:05:24 | autor: operator | tipo: chore | summary: normalized review timestamps into new column eviewed_at_utc and updated app to write UTC
Detalhes:
- Executado: migration script que criou backup e populou eviews.reviewed_at_utc com timestamps normalizados em UTC (ISO 8601).
- Backup criado: C:\Users\Pichau\analise_progress\ml_devolucoes.db.bak_20251027_100524
- Linhas atualizadas: 2 (valores populados em eviewed_at_utc)
- Alterações de código aplicadas:
  - pp_streamlit.py: set_review() agora grava timestamps em UTC; adicionado UI para editar/desmarcar revisões.
Arquivos afetados:
- app_streamlit.py (modificado: grava UTC em set_review, adiciona editor de revisões na UI)
- scripts/review_migration_runtime.py (script temporário executado para migração)
Resultado: eviews preserva o valor original em eviewed_at e agora tem eviewed_at_utc canônico em UTC para consultas e exibição consistente.
Rollback: arquivo de backup acima. Para reverter, restaurar o backup sobre ml_devolucoes.db.
