import os
import hashlib
import pandas as pd

COLUMNAS_REQUERIDAS = {"ID_chofer", "Nombre", "Transporte"}

# =====================================================
# Utils
# =====================================================
def _table_columns(conn, table_name: str) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =====================================================
# IMPORTACIÓN DESDE EXCEL
# =====================================================
def importar_choferes_desde_excel(conn, ruta_excel: str):
    df = pd.read_excel(ruta_excel)

    if not COLUMNAS_REQUERIDAS.issubset(df.columns):
        faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
        raise ValueError(f"Faltan columnas en Choferes: {faltantes}")

    cols = _table_columns(conn, "choferes")
    usa_transporte = "transporte" in cols

    cur = conn.cursor()

    for _, row in df.iterrows():
        id_chofer = row["ID_chofer"]

        if pd.isna(id_chofer):
            continue

        nombre = str(row["Nombre"]).strip()
        transporte = str(row["Transporte"]).strip()

        if usa_transporte:
            cur.execute("""
                INSERT INTO choferes (id_chofer, nombre, transporte, activo)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(id_chofer) DO UPDATE SET
                    nombre = excluded.nombre,
                    transporte = excluded.transporte,
                    activo = 1
            """, (
                str(id_chofer).strip(),
                nombre,
                transporte
            ))
        else:
            cur.execute("""
                INSERT INTO choferes (id_chofer, nombre, activo)
                VALUES (?, ?, 1)
                ON CONFLICT(id_chofer) DO UPDATE SET
                    nombre = excluded.nombre,
                    activo = 1
            """, (
                str(id_chofer).strip(),
                nombre
            ))

    conn.commit()


# =====================================================
# CONSULTAS
# =====================================================
def listar_choferes(conn, solo_activos=True):
    """
    SIEMPRE devuelve lista de dicts.
    Evita pantallas vacías por Rows no iterables.
    """
    cur = conn.cursor()

    if solo_activos:
        cur.execute("""
            SELECT id_chofer, nombre, activo
            FROM choferes
            WHERE activo = 1
            ORDER BY nombre
        """)
    else:
        cur.execute("""
            SELECT id_chofer, nombre, activo
            FROM choferes
            ORDER BY nombre
        """)

    rows = cur.fetchall()
    return [dict(r) for r in rows]


def desactivar_chofer(conn, id_chofer):
    cur = conn.cursor()
    cur.execute(
        "UPDATE choferes SET activo = 0 WHERE id_chofer = ?",
        (id_chofer,)
    )
    conn.commit()


# =====================================================
# IMPORTAR SOLO SI CAMBIÓ
# =====================================================
def importar_si_cambio(conn, ruta_excel: str, nombre_maestro: str = "choferes"):
    if not os.path.exists(ruta_excel):
        return False, f"No existe el archivo: {ruta_excel}"

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
    hash_anterior = row[0] if row else None

    if hash_anterior == hash_actual:
        return False, "Sin cambios"

    importar_choferes_desde_excel(conn, ruta_excel)

    cur.execute("""
        INSERT INTO meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (f"{nombre_maestro}_hash", hash_actual))

    conn.commit()
    return True, "Importado / actualizado"
