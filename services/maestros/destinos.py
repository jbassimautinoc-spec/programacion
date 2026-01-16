import pandas as pd
import os
import hashlib

COLUMNAS_REQUERIDAS = {"ID_Destino", "Destino"}


# =====================================================
# TABLA
# =====================================================
def crear_tabla_destinos(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS destinos (
        id_destino TEXT PRIMARY KEY,
        destino TEXT NOT NULL,
        activo INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()


# =====================================================
# IMPORTAR DESDE EXCEL
# =====================================================
def importar_destinos_desde_excel(conn, ruta_excel: str):
    df = pd.read_excel(ruta_excel)

    if not COLUMNAS_REQUERIDAS.issubset(df.columns):
        faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
        raise ValueError(f"Faltan columnas en Destinos: {faltantes}")

    crear_tabla_destinos(conn)
    cur = conn.cursor()

    for _, row in df.iterrows():
        id_destino = row["ID_Destino"]

        if pd.isna(id_destino):
            continue

        cur.execute("""
        INSERT INTO destinos (id_destino, destino, activo)
        VALUES (?, ?, 1)
        ON CONFLICT(id_destino) DO UPDATE SET
            destino = excluded.destino,
            activo = 1
        """, (
            str(id_destino).strip(),
            str(row["Destino"]).strip()
        ))

    conn.commit()


# =====================================================
# HASH
# =====================================================
def _file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =====================================================
# IMPORTAR SOLO SI CAMBIÓ
# =====================================================
def importar_si_cambio(conn, ruta_excel: str, nombre_maestro: str = "destinos"):
    if not os.path.exists(ruta_excel):
        return False, "No existe el archivo"

    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    conn.commit()

    hash_actual = _file_hash(ruta_excel)

    cur.execute(
        "SELECT value FROM meta WHERE key = ?",
        (f"{nombre_maestro}_hash",)
    )
    row = cur.fetchone()
    hash_anterior = row["value"] if row else None

    if hash_anterior == hash_actual:
        return False, "Sin cambios"

    importar_destinos_desde_excel(conn, ruta_excel)

    cur.execute("""
    INSERT INTO meta (key, value)
    VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (f"{nombre_maestro}_hash", hash_actual))

    conn.commit()
    return True, "Importado/actualizado"


# =====================================================
# LISTADO
# =====================================================
def listar_destinos(conn, solo_activos=True):
    crear_tabla_destinos(conn)
    cur = conn.cursor()

    if solo_activos:
        cur.execute(
            "SELECT * FROM destinos WHERE activo = 1 ORDER BY destino"
        )
    else:
        cur.execute(
            "SELECT * FROM destinos ORDER BY destino"
        )

    return cur.fetchall()
