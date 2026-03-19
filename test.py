import urllib.request
import json

try:
    req = urllib.request.Request('http://localhost:8000/api/admin/gebaeude_typen/1')
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8'))
except Exception as e:
    print(e)
