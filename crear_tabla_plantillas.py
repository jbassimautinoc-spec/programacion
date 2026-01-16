from utils.db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS plantillas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    id_material TEXT NOT NULL,
    id_cliente TEXT,
    id_origen TEXT,
    id_destino TEXT,
    observacion TEXT,
    activo INTEGER DEFAULT 1
)
""")

conn.commit()
conn.close()

print("OK - tabla plantillas creada en programacion_bca.sqlite")
