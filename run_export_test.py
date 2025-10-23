import sys, os
sys.path.insert(0, r'C:\Users\Pichau\analise_progress')

from app_streamlit import create_xlsx_export, load_financials

out = os.path.join(r'C:\Users\Pichau\analise_progress','reports','test_export_streamlit_option2.xlsx')

try:
    df = load_financials(only_pending=False)
    df = df.head(10)
except Exception as e:
    print('LOAD_ERROR', e)
    raise

try:
    create_xlsx_export(df, out, display_names=None)
    print('EXPORT_OK', out)
except Exception as e:
    print('EXPORT_ERROR', e)
    raise
