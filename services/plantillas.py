# services/plantillas.py
#
# Gestión real de plantillas de viaje
# Usa tabla: plantillas

# =================================================
# LISTAR PLANTILLAS ACTIVAS
# =================================================
def listar_plantillas(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            p.id,
            p.nombre,
            p.id_material,
            p.id_cliente,
            p.id_origen,
            p.id_destino,
            p.observacion
        FROM plantillas p
        WHERE p.activo = 1
        ORDER BY p.nombre
    """)
    return [dict(r) for r in cur.fetchall()]


# =================================================
# OBTENER UNA PLANTILLA
# =================================================
def get_plantilla(conn, id_plantilla):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id,
            nombre,
            id_material,
            id_cliente,
            id_origen,
            id_destino,
            observacion
        FROM plantillas
        WHERE id = ?
          AND activo = 1
    """, (id_plantilla,))
    row = cur.fetchone()
    return dict(row) if row else None


# =================================================
# CREAR PLANTILLA
# =================================================
def crear_plantilla(
    conn,
    nombre,
    material_id,
    cliente_id=None,
    origen_id=None,
    destino_id=None,
    observacion=None,
):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO plantillas (
            nombre,
            id_material,
            id_cliente,
            id_origen,
            id_destino,
            observacion,
            activo
        )
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (
        nombre,
        material_id,
        cliente_id,
        origen_id,
        destino_id,
        observacion
    ))
    conn.commit()
    return cur.lastrowid


# =================================================
# DESACTIVAR PLANTILLA
# =================================================
def desactivar_plantilla(conn, id_plantilla):
    cur = conn.cursor()
    cur.execute("""
        UPDATE plantillas
        SET activo = 0
        WHERE id = ?
    """, (id_plantilla,))
    conn.commit()
    return cur.rowcount > 0
