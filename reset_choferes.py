import sqlite3

conn = sqlite3.connect("data/programacion.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS choferes")
conn.commit()

print("Tabla choferes eliminada")

conn.close()
