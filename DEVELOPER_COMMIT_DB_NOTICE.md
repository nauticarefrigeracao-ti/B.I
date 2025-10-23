Decision: Commit `ml_devolucoes.db`

You requested the SQLite database be included in the repository to make the Streamlit deploy behave exactly like your local environment.

Notes and trade-offs:
- This file is a binary and will increase the repository size.
- Consider replacing it with a managed DB (Supabase/Postgres) later for production.
- To stop tracking the DB in the future, run:

  git rm --cached ml_devolucoes.db
  echo "ml_devolucoes.db" >> .gitignore

If you want me to add git-lfs support instead, I can do that (recommended for large binaries).
