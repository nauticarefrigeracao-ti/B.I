import urllib.request

urls = [
    'http://127.0.0.1:8501/assets/logo_center_v2.svg',
    'http://127.0.0.1:8501/'
]

for u in urls:
    print('\nREQUEST =>', u)
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'curl/7.64.1'})
        with urllib.request.urlopen(req, timeout=5) as r:
            status = getattr(r, 'status', None) or (r.getcode() if hasattr(r, 'getcode') else None)
            print('STATUS', status)
            ct = r.getheader('Content-Type')
            print('CONTENT-TYPE', ct)
            data = r.read(2048)
            print('BYTES_READ', len(data))
            text = None
            if ct and 'text' in ct or u.endswith('.svg'):
                text = data.decode('utf-8', errors='replace')
                print('BODY START:\n', text[:1000])
            else:
                print('BODY (binary) first bytes:', data[:80])
    except Exception as e:
        print('ERROR', type(e).__name__, e)

print('\nFinished checks')
