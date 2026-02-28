import sqlite3
import json

conn = sqlite3.connect("verbrannte_zone.db")
c = conn.cursor()

holz_prod = json.dumps([{"ressource": "Bauholz", "menge": 10}])
c.execute("UPDATE gebaeude_typen SET produktion=? WHERE name='Holzfäller'", (holz_prod,))

saege_ver = json.dumps([{"ressource": "Bauholz", "menge": 5}])
saege_prod = json.dumps([{"ressource": "Bretter", "menge": 5}])
c.execute("UPDATE gebaeude_typen SET rohstoffverbrauch=?, produktion=? WHERE name='Sägegrube'", (saege_ver, saege_prod))

conn.commit()
conn.close()
print("Produktion in DB injiziert!")
