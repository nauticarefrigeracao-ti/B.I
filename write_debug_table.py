from app_streamlit import load_financials, render_interactive_table
from pathlib import Path

out_dir = Path('reports')
out_dir.mkdir(parents=True, exist_ok=True)

df = load_financials(month='2025-09', only_loss=True)
if df is None or df.empty:
    print('NO DATA')
else:
    sample = df.head(200).copy()
    # format date for display
    if 'data_venda' in sample.columns:
        sample['data_venda'] = sample['data_venda'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
    # ensure index column exists
    sample.insert(0, '#', range(1,1+len(sample)))
    html = render_interactive_table(sample, table_id='debug_tbl')
    out = out_dir / 'debug_table.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('WROTE', out)
