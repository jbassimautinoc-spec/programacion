import sqlite3
from utils.db import get_connection

conn = get_connection()
cur = conn.cursor()

try:
    cur.execute("""
        ALTER TABLE programacion_semanal
        ADD COLUMN creado_por TEXT
    """)
    conn.commit()
    print("✔ Columna creado_por agregada correctamente")
except Exception as e:
    print("⚠ Ya existe o no se pudo agregar:", e)

conn.close()
