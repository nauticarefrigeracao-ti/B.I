from app_streamlit import load_financials
from datetime import datetime

start = '2025-09-01'
end = '2025-09-30'
# load_financials supports month slicing by YYYY-MM; we'll use month '2025-09'
month = '2025-09'

# we want only_loss=True to get devoluções com prejuízo
df = load_financials(month=month, only_pending=False, only_loss=True)

# filter by date between start and end (inclusive) — data_venda is datetime
if 'data_venda' in df.columns:
    df_slice = df[(df['data_venda'] >= start) & (df['data_venda'] <= end)]
else:
    df_slice = df

rows = len(df_slice)
unique_orders = df_slice['order_id'].nunique() if 'order_id' in df_slice.columns else 0
sum_prejuizo_real = df_slice['prejuizo_real_signed'].sum() if 'prejuizo_real_signed' in df_slice.columns else 0.0
sum_prejuizo_pendente = df_slice['prejuizo_pendente_calc'].sum() if 'prejuizo_pendente_calc' in df_slice.columns else 0.0

print('DATE_SLICE', month, start, '->', end)
print('ROWS_RETURNED', rows)
print('UNIQUE_ORDERS', unique_orders)
print('SUM_PREJUIZO_REAL_SIGNED', sum_prejuizo_real)
print('SUM_PREJUIZO_PENDENTE_MAGNITUDE', sum_prejuizo_pendente)
