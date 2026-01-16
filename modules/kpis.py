from datetime import date


# =========================
# KPIs DIARIOS
# =========================
def kpis_dia(conn, fecha: date):
    cur = conn.cursor()

    def q(sql):
        cur.execute(sql, (fecha.isoformat(),))
        return cur.fetchone()[0] or 0

    return {
        "total": q("SELECT COUNT(*) FROM lineas_dia WHERE fecha = ?"),
        "confirmados": q("""
            SELECT COUNT(*) FROM lineas_dia
            WHERE fecha = ? AND estado = 'CONFIRMADO'
        """),
        "cancelados": q("""
            SELECT COUNT(*) FROM lineas_dia
            WHERE fecha = ? AND estado = 'CANCELADO'
        """),
        "pendientes": q("""
            SELECT COUNT(*) FROM lineas_dia
            WHERE fecha = ? AND estado = 'PENDIENTE'
        """),
        "arena": q("""
            SELECT COUNT(*) FROM lineas_dia ld
            JOIN materiales m ON m.id_material = ld.material_id
            WHERE ld.fecha = ? AND ld.estado = 'CONFIRMADO' AND m.material = 'Arena'
        """),
        "piedra": q("""
            SELECT COUNT(*) FROM lineas_dia ld
            JOIN materiales m ON m.id_material = ld.material_id
            WHERE ld.fecha = ? AND ld.estado = 'CONFIRMADO' AND m.material = 'Piedra'
        """),
        "fuera_plan": q("""
            SELECT COUNT(*) FROM lineas_dia
            WHERE fecha = ? AND origen_linea = 'FUERA_DE_PLAN'
        """),
    }


# =========================
# KPIs SEMANALES
# =========================
def kpis_semana(conn, semana: str):
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado = 'CONFIRMADO' THEN 1 ELSE 0 END) AS confirmados,
            SUM(CASE WHEN estado = 'CANCELADO' THEN 1 ELSE 0 END) AS cancelados
        FROM lineas_dia
        WHERE strftime('%Y-W%W', fecha) = ?
    """, (semana,))

    row = cur.fetchone()
    return dict(row) if row else {
        "total": 0,
        "confirmados": 0,
        "cancelados": 0
    }
