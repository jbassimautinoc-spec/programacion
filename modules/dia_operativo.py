from __future__ import annotations
from datetime import date

# -------------------------------------------------
# Obtener líneas del día
# -------------------------------------------------
def obtener_lineas_del_dia(conn, fecha: date):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            l.id            AS id,
            l.id            AS id_linea,
            l.fecha         AS fecha,
            l.estado        AS estado,
            l.origen_linea  AS origen_linea,

            l.id_chofer     AS id_chofer,
            ch.nombre       AS chofer,

            l.id_tractor    AS id_tractor,
            t.patente       AS tractor,

            l.id_material   AS id_material
        FROM lineas_dia l
        LEFT JOIN choferes  ch ON ch.id_chofer  = l.id_chofer
        LEFT JOIN tractores t  ON t.id_tractor = l.id_tractor
        WHERE DATE(l.fecha) = DATE(?)
        ORDER BY ch.nombre IS NULL, ch.nombre
    """, (fecha.isoformat(),))

    return [dict(r) for r in cur.fetchall()]


# -------------------------------------------------
# KPIs del día
# -------------------------------------------------
def kpis_dia(conn, fecha: date):
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado = 'CONFIRMADO' THEN 1 ELSE 0 END) AS confirmados,
            SUM(CASE WHEN estado = 'CANCELADO'  THEN 1 ELSE 0 END) AS cancelados,
            SUM(CASE WHEN estado = 'PENDIENTE'  THEN 1 ELSE 0 END) AS pendientes,
            SUM(CASE WHEN origen_linea = 'FUERA_DE_PLAN' THEN 1 ELSE 0 END) AS fuera_plan
        FROM lineas_dia
        WHERE DATE(fecha) = DATE(?)
    """, (fecha.isoformat(),))

    r = cur.fetchone()

    def v(row, key, idx):
        try:
            return row[key] or 0
        except Exception:
            return row[idx] or 0

    return {
        "total":       v(r, "total", 0),
        "confirmados": v(r, "confirmados", 1),
        "cancelados":  v(r, "cancelados", 2),
        "pendientes":  v(r, "pendientes", 3),
        "fuera_plan":  v(r, "fuera_plan", 4),
        "arena":       0,
        "piedra":      0,
    }


# -------------------------------------------------
# Acciones sobre líneas
# -------------------------------------------------
def confirmar_linea(conn, id_linea: int, usuario: str):
    cur = conn.cursor()
    cur.execute("""
        UPDATE lineas_dia
        SET estado = 'CONFIRMADO'
        WHERE id = ?
    """, (id_linea,))
    conn.commit()


def cancelar_linea(conn, id_linea: int, usuario: str):
    cur = conn.cursor()
    cur.execute("""
        UPDATE lineas_dia
        SET estado = 'CANCELADO'
        WHERE id = ?
    """, (id_linea,))
    conn.commit()


# -------------------------------------------------
# Crear fuera de programación
# -------------------------------------------------
def crear_fuera_de_programacion(
    conn,
    fecha: date,
    id_chofer: str,
    id_tractor: str,
    id_material: str,
    usuario: str
):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lineas_dia (
            fecha,
            id_chofer,
            id_tractor,
            id_material,
            estado,
            origen_linea,
            creado_por
        )
        VALUES (?, ?, ?, ?, 'PENDIENTE', 'FUERA_DE_PLAN', ?)
    """, (
        fecha.isoformat(),
        id_chofer,
        id_tractor,
        id_material,
        usuario,
    ))
    conn.commit()
