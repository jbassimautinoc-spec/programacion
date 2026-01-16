import sqlite3

conn = sqlite3.connect("data/programacion.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE choferes ADD COLUMN transporte TEXT")
    print("Columna transporte agregada")
except Exception as e:
    print("Aviso:", e)

conn.commit()
conn.close()

import sqlite3

conn = sqlite3.connect("data/programacion.db")
cur = conn.cursor()

for tabla in ["materiales", "clientes", "tractores", "origenes", "destinos"]:
    try:
        cur.execute(f"ALTER TABLE {tabla} ADD COLUMN activo INTEGER DEFAULT 1")
        print(f"Columna activo agregada en {tabla}")
    except Exception as e:
        print(f"{tabla}: {e}")

conn.commit()
conn.close()
