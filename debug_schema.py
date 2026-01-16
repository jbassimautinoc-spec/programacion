import sqlite3

DB_PATH = "data/programacion_bca.sqlite"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

tablas = [
    "choferes",
    "tractores",
    "lineas_dia",
    "lineas_programacion",
    "viajes",
    "eventos",
    "plantillas",
]

for tabla in tablas:
    print("\n==============================")
    print(f"TABLA: {tabla}")
    try:
        cur.execute(f"PRAGMA table_info({tabla});")
        rows = cur.fetchall()
        if not rows:
            print("⚠️ Tabla no existe o sin columnas")
        for r in rows:
            # r = (cid, name, type, notnull, dflt_value, pk)
            print(r)
    except Exception as e:
        print("❌ ERROR:", e)

conn.close()
