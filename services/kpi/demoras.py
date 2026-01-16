from datetime import date

# Tipos válidos de demoras
TIPOS_DEMORA = (
    "DEMORA_CARGA",
    "DEMORA_DESCARGA",
    "DEMORA_CHOFER",
)

# =================================================
# KPI: DEMORAS POR VIAJE
# =================================================
def kpi_demoras_por_viaje(conn, viaje_id: str):
    """
    Devuelve minutos de demora por tipo y total para un viaje.
    """
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            tipo,
            SUM(
                (JULIANDAY(fin_ts) - JULIANDAY(inicio_ts)) * 24 * 60
            ) AS minutos
        FROM eventos_viaje
        WHERE viaje_id = ?
          AND tipo IN {TIPOS_DEMORA}
        GROUP BY tipo
    """, (viaje_id,))

    data = {r["tipo"]: int(r["minutos"] or 0) for r in cur.fetchall()}

    return {
        "demora_carga": data.get("DEMORA_CARGA", 0),
        "demora_descarga": data.get("DEMORA_DESCARGA", 0),
        "demora_chofer": data.get("DEMORA_CHOFER", 0),
        "total": sum(data.values()),
    }


# =================================================
# KPI: DEMORAS POR DÍA
# =================================================
def kpi_demoras_por_dia(conn, fecha: date):
    """
    Devuelve demoras acumuladas del día.
    """
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            e.tipo,
            SUM(
                (JULIANDAY(e.fin_ts) - JULIANDAY(e.inicio_ts)) * 24 * 60
            ) AS minutos
        FROM eventos_viaje e
        JOIN viajes v ON v.id_viaje = e.viaje_id
        WHERE DATE(v.fecha) = DATE(?)
          AND e.tipo IN {TIPOS_DEMORA}
        GROUP BY e.tipo
    """, (fecha,))

    data = {r["tipo"]: int(r["minutos"] or 0) for r in cur.fetchall()}

    return {
        "fecha": fecha,
        "demora_carga": data.get("DEMORA_CARGA", 0),
        "demora_descarga": data.get("DEMORA_DESCARGA", 0),
        "demora_chofer": data.get("DEMORA_CHOFER", 0),
        "total": sum(data.values()),
    }


# =================================================
# KPI: DEMORAS POR CLIENTE
# =================================================
def kpi_demoras_por_cliente(conn, desde, hasta):
    """
    Devuelve demoras agrupadas por cliente.
    """
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            c.cliente,
            SUM(
                (JULIANDAY(e.fin_ts) - JULIANDAY(e.inicio_ts)) * 24 * 60
            ) AS minutos
        FROM eventos_viaje e
        JOIN viajes v   ON v.id_viaje = e.viaje_id
        JOIN clientes c ON c.id_cliente = v.cliente_id
        WHERE DATE(v.fecha) BETWEEN DATE(?) AND DATE(?)
          AND e.tipo IN {TIPOS_DEMORA}
        GROUP BY c.cliente
        ORDER BY minutos DESC
    """, (desde, hasta))

    return [
        {
            "cliente": r["cliente"],
            "minutos_demora": int(r["minutos"] or 0),
        }
        for r in cur.fetchall()
    ]
