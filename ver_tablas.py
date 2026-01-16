from utils.db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
SELECT name FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

print("TABLAS EN LA BASE:")
for r in cur.fetchall():
    print("-", r[0])

conn.close()
