from utils.db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("TABLAS:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT COUNT(*) FROM choferes")
print("Choferes OK")

cur.execute("SELECT COUNT(*) FROM materiales")
print("Materiales OK")

conn.close()
