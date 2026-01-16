import pandas as pd
import os
import hashlib

# =====================================================
# BOOTSTRAP DEFENSIVO (ÚLTIMA LÍNEA DE DEFENSA)
# =====================================================
def _asegurar_tabla_tractores(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tractores (
        id_tractor TEXT PRIMARY KEY,
        patente TEXT NOT NULL,
        activo INTEGER DEFAULT 1,
        tipo_flota TEXT DEFAULT 'PROPIA',
        estado TEXT DEFAULT 'OPERATIVO'
    )
    """)
    conn.commit()


COLUMNAS_REQUERIDAS = {"ID_Tractor", "Patente"}


# =====================================================
# Utils
# =====================================================
def _file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =====================================================
# IMPORTAR DESDE EXCEL
# =====================================================
def importar_tractores_desde_excel(conn, ruta_excel: str):
    _asegurar_tabla_tractores(conn)  # 🔥 CLAVE

    df = pd.read_excel(ruta_excel)
    ...

    df = pd.read_excel(ruta_excel)

    if not COLUMNAS_REQUERIDAS.issubset(df.columns):
        faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
        raise ValueError(f"Faltan columnas en Tractores: {faltantes}")

    cur = conn.cursor()

    for _, row in df.iterrows():
        id_tractor = row["ID_Tractor"]

        if pd.isna(id_tractor):
            continue

        patente = str(row["Patente"]).strip()

        cur.execute("""
            INSERT INTO tractores (
                id_tractor,
                patente,
                activo,
                tipo_flota,
                estado
            )
            VALUES (?, ?, 1, 'PROPIA', 'OPERATIVO')
            ON CONFLICT(id_tractor) DO UPDATE SET
                patente   = excluded.patente,
                activo    = 1
        """, (
            str(id_tractor).strip(),
            patente
        ))

    conn.commit()


# =====================================================
# IMPORTAR SOLO SI CAMBIÓ
# =====================================================
def importar_si_cambio(conn, ruta_excel: str, nombre_maestro: str = "tractores"):
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

    importar_tractores_desde_excel(conn, ruta_excel)

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
def listar_tractores(conn, solo_activos: bool = True):
    """
    Devuelve lista de tractores como dict (no sqlite3.Row)
    """

    cur = conn.cursor()
    where_activo = "WHERE t.activo = 1" if solo_activos else ""

    cur.execute(f"""
        SELECT
            t.*,
            c.id_chofer AS id_chofer
        FROM tractores t
        LEFT JOIN (
            SELECT
                id_tractor,
                MIN(id_chofer) AS id_chofer
            FROM choferes
            WHERE activo = 1
              AND id_tractor IS NOT NULL
            GROUP BY id_tractor
        ) c ON c.id_tractor = t.id_tractor
        {where_activo}
        ORDER BY t.patente
    """)

    return [dict(r) for r in cur.fetchall()]
