import uuid
from datetime import date

from services.eventos import chofer_disponible


# =================================================
# LISTAR LÍNEAS PENDIENTES PARA GENERAR VIAJE
# =================================================
def listar_lineas_para_viajes(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            ld.id                AS id_linea,
            ld.fecha,
            ld.id_chofer,
            ch.nombre            AS chofer,
            ld.id_material,
            m.material           AS material,
            COALESCE(t.patente, 'Sin tractor') AS tractor,
            ld.origen_linea,
            ld.estado
        FROM lineas_dia ld
        LEFT JOIN viajes v
               ON v.linea_id = ld.id
        LEFT JOIN choferes ch
               ON ch.id_chofer = ld.id_chofer
        LEFT JOIN materiales m
               ON m.id_material = ld.id_material
        LEFT JOIN tractores t
               ON t.id_tractor = ch.id_tractor
        WHERE ld.estado = 'PENDIENTE'
          AND ld.origen_linea IN ('PROGRAMACION', 'FUERA_DE_PLAN')
          AND v.id IS NULL
        ORDER BY ld.fecha, ld.id
    """)
    return [dict(r) for r in cur.fetchall()]




# =================================================
# CONFIRMAR LÍNEA Y GENERAR VIAJE
# =================================================
def confirmar_linea_y_generar_viaje(
    conn,
    id_linea,
    origen_linea,
    fecha,
    chofer_id,
    cliente_id,
    material_id,
    origen_id,
    destino_id,
    id_plantilla,
    observacion,
    usuario,
):
    cur = conn.cursor()

    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)

    if not chofer_disponible(conn, chofer_id, fecha):
        raise ValueError("❌ El chofer está de FRANCO. No se puede generar el viaje.")

    cur.execute("""
        SELECT t.id_tractor, t.estado
        FROM choferes c
        LEFT JOIN tractores t ON t.id_tractor = c.id_tractor
        WHERE c.id_chofer = ?
    """, (chofer_id,))
    row = cur.fetchone()

    tractor_id = None
    if row and row["id_tractor"]:
        if row["estado"] != "OPERATIVO":
            raise ValueError("El tractor no está OPERATIVO.")
        tractor_id = row["id_tractor"]

    cur.execute("BEGIN IMMEDIATE;")

    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM viajes;")
    nro_viaje = cur.fetchone()[0]

    id_viaje = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO viajes (
            id,
            fecha,
            id_chofer,
            id_tractor,
            id_cliente,
            id_material,
            id_origen,
            id_destino,
            origen_viaje,
            id_plantilla,
            estado,
            creado_por,
            linea_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMADO', ?, ?)
    """, (
        nro_viaje,
        fecha,
        chofer_id,
        tractor_id,
        cliente_id,
        material_id,
        origen_id,
        destino_id,
        origen_linea,
        id_plantilla,
        usuario,
        id_linea
    ))

    cur.execute("""
        UPDATE lineas_dia
        SET estado = 'GENERADO'
        WHERE id = ?
    """, (id_linea,))

    conn.commit()
    return id_viaje


# =================================================
# LISTAR VIAJES (HISTÓRICO)
# =================================================
def listar_viajes(conn, desde=None, hasta=None):
    cur = conn.cursor()
    where = []
    params = []

    if desde:
        where.append("DATE(v.fecha) >= DATE(?)")
        params.append(desde)

    if hasta:
        where.append("DATE(v.fecha) <= DATE(?)")
        params.append(hasta)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    cur.execute(f"""
        SELECT
            v.id,
            v.fecha,
            ch.nombre     AS chofer,
            t.patente     AS tractor,
            c.cliente     AS cliente,
            m.material    AS material,
            o.origen      AS origen,
            d.destino     AS destino,
            v.estado
        FROM viajes v
        LEFT JOIN choferes   ch ON ch.id_chofer   = v.id_chofer
        LEFT JOIN tractores  t  ON t.id_tractor  = v.id_tractor
        LEFT JOIN clientes   c  ON c.id_cliente  = v.id_cliente
        LEFT JOIN materiales m  ON m.id_material = v.id_material
        LEFT JOIN origenes   o  ON o.id_origen   = v.id_origen
        LEFT JOIN destinos   d  ON d.id_destino  = v.id_destino
        {where_sql}
        ORDER BY DATE(v.fecha) DESC, v.id DESC
    """, params)

    return [dict(r) for r in cur.fetchall()]


# =================================================
# LISTAR VIAJES ACTIVOS (EVENTOS)
# =================================================
def listar_viajes_activos(conn, desde=None, hasta=None):
    cur = conn.cursor()
    where = ["v.estado IN ('CONFIRMADO', 'OPERATIVO')"]
    params = []

    if desde:
        where.append("DATE(v.fecha) >= DATE(?)")
        params.append(desde)

    if hasta:
        where.append("DATE(v.fecha) <= DATE(?)")
        params.append(hasta)

    where_sql = f"WHERE {' AND '.join(where)}"

    cur.execute(f"""
        SELECT
            v.id,
            v.fecha,
            ch.nombre  AS chofer,
            m.material AS material,
            t.patente  AS tractor,
            v.estado
        FROM viajes v
        LEFT JOIN choferes   ch ON ch.id_chofer   = v.id_chofer
        LEFT JOIN tractores  t  ON t.id_tractor  = v.id_tractor
        LEFT JOIN materiales m  ON m.id_material = v.id_material
        {where_sql}
        ORDER BY DATE(v.fecha) DESC
    """, params)

    return [dict(r) for r in cur.fetchall()]


# =================================================
# FINALIZAR VIAJE
# =================================================
def finalizar_viaje(conn, viaje_id, usuario):
    cur = conn.cursor()
    cur.execute("""
        UPDATE viajes
        SET estado = 'FINALIZADO'
        WHERE id = ?
    """, (viaje_id,))
    conn.commit()
