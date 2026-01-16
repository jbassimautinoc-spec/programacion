from datetime import datetime, date


def listar_eventos_globales(
    conn,
    desde,
    hasta,
    tipo=None,
    chofer_id=None,
    tractor_id=None  # reservado para milestone futuro
):
    """
    Lista eventos globales de viajes.
    Incluye nombre de chofer (JOIN con maestros).
    """

    if desde is None:
        desde = date(1900, 1, 1)
    if hasta is None:
        hasta = date(2100, 12, 31)

    cur = conn.cursor()
    cur.execute("""
        SELECT
            e.id_evento,
            e.tipo,
            e.inicio_ts,
            e.fin_ts,
            e.observacion,
            e.creado_por,
            e.creado_en,
            v.fecha,
            v.id_chofer,
            c.nombre AS chofer_nombre
        FROM eventos_viaje e
        JOIN viajes v ON v.id = e.viaje_id
        LEFT JOIN choferes c ON c.id_chofer = v.id_chofer
    """)

    rows = [dict(r) for r in cur.fetchall()]
    eventos = []

    for r in rows:
        inicio = datetime.fromisoformat(r["inicio_ts"])
        fin = datetime.fromisoformat(r["fin_ts"]) if r["fin_ts"] else None

        # filtro fechas
        if not (desde <= inicio.date() <= hasta):
            continue

        # filtro tipo
        if tipo:
            tipo_db = tipo.upper().replace(" ", "_")
            if r["tipo"] != tipo_db:
                continue

        # filtro chofer
        if chofer_id is not None and r["id_chofer"] != chofer_id:
            continue

        r["duracion_min"] = (
            int((fin - inicio).total_seconds() // 60) if fin else None
        )

        eventos.append(r)

    return eventos
