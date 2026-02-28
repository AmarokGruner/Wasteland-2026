import asyncio
from main import get_db

conn = get_db()
cur = conn.cursor()

cur.execute("SELECT id, name FROM gebaeude_typen WHERE name IN ('Holzfäller', 'Sägegrube')")
print("Gebäude Typen:", cur.fetchall())

cur.execute("SELECT * FROM buildings")
print("Buildings:", cur.fetchall())

cur.execute("SELECT * FROM provinzen")
print("Provinzen:", cur.fetchall())

cur.execute("SELECT * FROM provinz_lager")
print("Lager:", cur.fetchall())

cur.execute("SELECT * FROM ressourcen WHERE name='Bauholz'")
print("Ressource:", cur.fetchall())

conn.close()
