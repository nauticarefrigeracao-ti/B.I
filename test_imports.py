try:
    import matplotlib
    print('MATPLOTLIB_OK', matplotlib.__version__)
except Exception as e:
    print('MATPLOTLIB_ERROR', e)
try:
    import altair
    print('ALT_Available', altair.__version__)
except Exception as e:
    print('ALT_ERROR', e)
