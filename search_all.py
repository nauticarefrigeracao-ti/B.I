import os
for root,dirs,files in os.walk('.'):
    for f in files:
        if f.endswith('.py'):
            path=os.path.join(root,f)
            with open(path,encoding='utf-8') as fh:
                for i,l in enumerate(fh, start=1):
                    if 'bar_chart(' in l or 'line_chart(' in l:
                        print(path, i, l.strip())
