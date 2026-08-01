import urllib.request
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/buscar-produtos/?tipo=simples')
    res = urllib.request.urlopen(req).read()
    print("SUCCESS")
except Exception as e:
    print("ERROR", getattr(e, 'code', str(e)))
