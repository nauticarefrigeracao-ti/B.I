from app_streamlit import load_financials, render_interactive_table
import pandas as pd

df = load_financials(month='2025-09', only_loss=True)
if df is None:
    print('LOAD_NONE')
else:
    sample = df.head(5).copy()
    # prepare display columns similar to app
    if 'data_venda' in sample.columns:
        sample['data_venda'] = sample['data_venda'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
    sample.insert(0, '#', range(1,1+len(sample)))
    html = render_interactive_table(sample, table_id='test_tbl')
    print('HTML_TYPE', type(html))
    if html is None:
        print('HTML_NONE')
    else:
        print('HTML_START')
        print(str(html)[:400])
        print('\n...')
