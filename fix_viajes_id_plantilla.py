import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "programacion_bca.sqlite"

print("Usando DB:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Mostrar columnas antes
print("ANTES:")
cur.execute("PRAGMA table_info(viajes)")
for r in cur.fetchall():
    print(r)

# Agregar columna si no existe
cur.execute("""
    ALTER TABLE viajes
    ADD COLUMN id_plantilla INTEGER
""")

conn.commit()

# Mostrar columnas después
print("\nDESPUÉS:")
cur.execute("PRAGMA table_info(viajes)")
for r in cur.fetchall():
    print(r)

conn.close()

print("\nOK - columna id_plantilla agregada")
