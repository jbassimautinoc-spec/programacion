print("BOOTSTRAP TEST ARRANCÓ")

from utils.db import get_connection

print("IMPORT OK")

conn = get_connection()
print("CONEXION OK")

cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("TABLAS:", tables)

conn.close()
print("FIN BOOTSTRAP")
