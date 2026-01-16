import sqlite3
from pathlib import Path
import os

print("CWD:", os.getcwd())

DB_PATH = Path(__file__).resolve().parent / "data" / "programacion_bca.sqlite"
print("DB_PATH:", DB_PATH)
print("EXISTE:", DB_PATH.exists())

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("\nTABLAS:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for t in cur.fetchall():
    print(" -", t[0])

print("\nCOLUMNAS DE VIAJES (ANTES):")
try:
    cur.execute("PRAGMA table_info(viajes)")
    cols = cur.fetchall()
    if not cols:
        print("❌ tabla viajes NO existe en esta base")
    for c in cols:
        print(c)
except Exception as e:
    print("ERROR:", e)

print("\nINTENTANDO ALTER TABLE...")
try:
    cur.execute("ALTER TABLE viajes ADD COLUMN id_plantilla INTEGER")
    conn.commit()
    print("✔ ALTER TABLE ejecutado")
except Exception as e:
    print("ERROR ALTER:", e)

print("\nCOLUMNAS DE VIAJES (DESPUÉS):")
cur.execute("PRAGMA table_info(viajes)")
for c in cur.fetchall():
    print(c)

conn.close()
print("\nFIN")
