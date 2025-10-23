from app_streamlit import load_financials

if __name__ == '__main__':
    df = load_financials(month='2025-09', only_loss=True)
    if df is None:
        print('DF_NONE')
    else:
        print('ROWS:', len(df))
        print('COLUMNS:', list(df.columns))
        print('HEAD 3:')
        for i, row in df.head(3).iterrows():
            print(dict(row))
