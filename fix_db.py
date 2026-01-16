from utils.db import get_connection
from utils.schema import init_db

conn = get_connection()
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS programacion_diaria;")
conn.commit()

init_db(conn)
conn.close()

print("OK: programacion_diaria recreada correctamente")

