from pathlib import Path
from utils.db import get_db_path, get_connection

db_path = get_db_path()

if db_path.exists():
    db_path.unlink()
    print("DB eliminada:", db_path)

conn = get_connection()
conn.close()
print("DB recreada y esquema OK:", db_path)
