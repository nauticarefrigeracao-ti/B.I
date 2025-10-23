"""
Cópia do script principal adaptado para o pacote de progresso.
"""

from pathlib import Path
import shutil

# copia o script original para o pacote
src = Path(r"C:\Users\Pichau\analisar_devolucoes.py")
dst = Path(r"C:\Users\Pichau\analise_progress\analisar_devolucoes.py")
if src.exists():
    shutil.copy(src, dst)

# copia table.xlsx e CSVs gerados
files_to_copy = [
    Path(r"C:\Users\Pichau\Downloads\table.xlsx"),
    Path(r"C:\Users\Pichau\pendentes.csv"),
    Path(r"C:\Users\Pichau\prejuizos.csv"),
]
for f in files_to_copy:
    if f.exists():
        shutil.copy(f, Path(r"C:\Users\Pichau\analise_progress") / f.name
)
print("Arquivos copiados para C:\\Users\\Pichau\\analise_progress")