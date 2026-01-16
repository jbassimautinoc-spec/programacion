import sqlite3

DB_PATH = "data/programacion_bca.sqlite"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    recurso_tipo TEXT NOT NULL,
    recurso_id INTEGER NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    observacion TEXT,
    creado_por TEXT
);
""")

conn.commit()
conn.close()

print("OK - tabla eventos creada")
