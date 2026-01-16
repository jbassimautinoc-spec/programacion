import pandas as pd
import os
import hashlib

COLUMNAS_REQUERIDAS = {"ID_Cliente", "Cliente"}

# =====================================================
# BOOTSTRAP DEFENSIVO
# =====================================================
def _asegurar_tabla_clientes(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente TEXT PRIMARY KEY,
        cliente TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)
    conn.commit()

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
def importar_clientes_desde_excel(conn, ruta_excel: str):
    _asegurar_tabla_clientes(conn)  # 🔥 CLAVE

    df = pd.read_excel(ruta_excel)

    if not COLUMNAS_REQUERIDAS.issubset(df.columns):
        faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
        raise ValueError(f"Faltan columnas en Clientes: {faltantes}")

    cur = conn.cursor()

    for _, row in df.iterrows():
        id_cliente = row["ID_Cliente"]

        if pd.isna(id_cliente):
            continue

        cliente = str(row["Cliente"]).strip()

        cur.execute("""
            INSERT INTO clientes (id_cliente, cliente, activo)
            VALUES (?, ?, 1)
            ON CONFLICT(id_cliente) DO UPDATE SET
                cliente = excluded.cliente,
                activo = 1
        """, (
            str(id_cliente).strip(),
            cliente
        ))

    conn.commit()

# =====================================================
# IMPORTAR SOLO SI CAMBIÓ
# =====================================================
def importar_si_cambio(conn, ruta_excel: str, nombre_maestro: str = "clientes"):
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

    importar_clientes_desde_excel(conn, ruta_excel)

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
def listar_clientes(conn, solo_activos=True):
    cur = conn.cursor()

    if solo_activos:
        cur.execute("""
            SELECT *
            FROM clientes
            WHERE activo = 1
            ORDER BY cliente
        """)
    else:
        cur.execute("""
            SELECT *
            FROM clientes
            ORDER BY cliente
        """)

    return cur.fetchall()
