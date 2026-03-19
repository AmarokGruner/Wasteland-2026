import urllib.request
import json
try:
    c1 = urllib.request.urlopen("http://localhost:8000/api/admin/terrain?token=null").read().decode("utf-8")
    print("TERRAIN:", c1[:200])
except Exception as e:
    print("TERRAIN ERROR:", e)

try:
    c2 = urllib.request.urlopen("http://localhost:8000/api/admin/regierungsformen?token=null").read().decode("utf-8")
    print("REGS:", c2[:200])
except Exception as e:
    print("REGS ERROR:", e)
