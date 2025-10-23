import sys
sys.path.insert(0, r'C:\Users\Pichau\analise_progress')
from app_streamlit import load_financials

df_all = load_financials()
df_loss = load_financials(only_loss=True)
print('ALL count:', len(df_all))
print('LOSS count:', len(df_loss))
if not df_loss.empty:
    print('LOSS totals min,max:', df_loss['total_brl'].min(), df_loss['total_brl'].max())
    assert df_loss['total_brl'].max() < 0 or df_loss['total_brl'].eq(0).all(), 'Found non-negative total in loss filter'
print('Quick check OK')
