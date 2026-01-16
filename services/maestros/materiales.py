import pandas as pd
import os
import hashlib

# =====================================================
# BOOTSTRAP DEFENSIVO
# =====================================================
def _asegurar_tabla_materiales(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS materiales (
        id_material TEXT PRIMARY KEY,
        material TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)
    conn.commit()

COLUMNAS_REQUERIDAS = {"ID_Material", "Material"}


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
# IMPORTAR DESDE EXCEL
# =====================================================
def importar_materiales_desde_excel(conn, ruta_excel):
    _asegurar_tabla_materiales(conn)  # 🔥 CLAVE

    df = pd.read_excel(ruta_excel)
    ...


    if not COLUMNAS_REQUERIDAS.issubset(df.columns):
        faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
        raise ValueError(f"Faltan columnas en Materiales: {faltantes}")

    cols = _table_columns(conn, "materiales")
    usa_activo = "activo" in cols

    cur = conn.cursor()

    for _, row in df.iterrows():
        id_material = row["ID_Material"]

        if pd.isna(id_material):
            continue

        material = str(row["Material"]).strip()

        if usa_activo:
            cur.execute("""
                INSERT INTO materiales (id_material, material, activo)
                VALUES (?, ?, 1)
                ON CONFLICT(id_material) DO UPDATE SET
                    material = excluded.material,
                    activo = 1
            """, (
                str(id_material).strip(),
                material
            ))
        else:
            cur.execute("""
                INSERT INTO materiales (id_material, material)
                VALUES (?, ?)
                ON CONFLICT(id_material) DO UPDATE SET
                    material = excluded.material
            """, (
                str(id_material).strip(),
                material
            ))

    conn.commit()


# =====================================================
# IMPORTAR SOLO SI CAMBIÓ
# =====================================================
def importar_si_cambio(conn, ruta_excel: str, nombre_maestro: str = "materiales"):
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
    hash_anterior = row[0] if row else None

    if hash_anterior == hash_actual:
        return False, "Sin cambios"

    importar_materiales_desde_excel(conn, ruta_excel)

    cur.execute("""
        INSERT INTO meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (f"{nombre_maestro}_hash", hash_actual))

    conn.commit()
    return True, "Importado / actualizado"


# =====================================================
# LISTADO
# =====================================================
def listar_materiales(conn, solo_activos=True):
    cur = conn.cursor()

    if solo_activos:
        cur.execute("""
            SELECT *
            FROM materiales
            WHERE activo = 1
            ORDER BY material
        """)
    else:
        cur.execute("""
            SELECT *
            FROM materiales
            ORDER BY material
        """)

    return cur.fetchall()
