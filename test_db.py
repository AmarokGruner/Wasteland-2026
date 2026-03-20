import sqlite3

c = sqlite3.connect('verbrannte_zone.db')
cur = c.cursor()
cur.execute('SELECT * FROM terrain_typen LIMIT 1')
row = cur.fetchone()
cols = [desc[0] for desc in cur.description]
print("TERRAIN:")
for i in range(len(cols)):
    print(f"  {cols[i]}: {row[i] if row else None}")

cur.execute('SELECT * FROM regierungsformen LIMIT 1')
row = cur.fetchone()
cols = [desc[0] for desc in cur.description]
print("\nREGS:")
for i in range(len(cols)):
    print(f"  {cols[i]}: {row[i] if row else None}")
