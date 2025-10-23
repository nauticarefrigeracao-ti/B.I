with open('app_streamlit.py', 'r', encoding='utf-8') as f:
    for i,l in enumerate(f, start=1):
        if 'st.bar_chart' in l or 'st.line_chart' in l:
            print(i, l.strip())
