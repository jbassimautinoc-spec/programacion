from datetime import date, timedelta

# =================================================
# Helpers de semana
# =================================================
def _lunes_de_semana(d: date) -> date:
    return d - timedelta(days=d.weekday())

def _domingo_de_semana(d: date) -> date:
    return _lunes_de_semana(d) + timedelta(days=6)

# =================================================
# DESVÍOS POR DÍA (DETALLE)
# =================================================
def calcular_desvios_dia(conn, fecha: date):
    """
    Compara líneas del día vs viajes ejecutados
    Match por: fecha + chofer
    """

    cur = conn.cursor()

    # -----------------------------
    # 1) Líneas del día (foto real)
    # -----------------------------
    cur.execute("""
        SELECT
            ld.fecha,
            ld.id_chofer,
            ch.nombre AS chofer_nombre,
            m.material AS material_programado
        FROM lineas_dia ld
        JOIN choferes ch ON ch.id_chofer = ld.id_chofer
        JOIN materiales m ON m.id_material = ld.id_material
        WHERE ld.fecha = ?
    """, (fecha.isoformat(),))

    programadas = [dict(r) for r in cur.fetchall()]
    prog_por_chofer = {p["id_chofer"]: p for p in programadas}

    # -----------------------------
    # 2) Viajes ejecutados
    # -----------------------------
    cur.execute("""
        SELECT
            v.fecha,
            v.id_chofer,
            m.material AS material_ejecutado
        FROM viajes v
        JOIN materiales m ON m.id_material = v.id_material
        WHERE v.fecha = ?
          AND v.estado IN ('CONFIRMADO', 'FINALIZADO')
    """, (fecha.isoformat(),))

    ejecutados = [dict(r) for r in cur.fetchall()]
    ejec_por_chofer = {e["id_chofer"]: e for e in ejecutados}

    # -----------------------------
    # 3) Comparación
    # -----------------------------
    resultados = []

    for chofer_id, prog in prog_por_chofer.items():
        ejec = ejec_por_chofer.get(chofer_id)

        if not ejec:
            resultado = "NO_EJECUTADO"
            material_ej = None
        elif prog["material_programado"] != ejec["material_ejecutado"]:
            resultado = "CAMBIO_MATERIAL"
            material_ej = ejec["material_ejecutado"]
        else:
            resultado = "OK"
            material_ej = ejec["material_ejecutado"]

        resultados.append({
            "fecha": fecha,
            "chofer_id": chofer_id,
            "chofer_nombre": prog["chofer_nombre"],
            "material_programado": prog["material_programado"],
            "material_ejecutado": material_ej,
            "resultado": resultado
        })

    return resultados

# =================================================
# RESUMEN SEMANAL (KPIs)
# =================================================
def calcular_resumen_semana(conn, fecha_base: date):
    """
    Desvío semanal:
    línea del día que NO terminó en viaje.
    """

    lunes = _lunes_de_semana(fecha_base)
    domingo = _domingo_de_semana(fecha_base)

    cur = conn.cursor()
    cur.execute("""
        SELECT
            ld.fecha,
            COUNT(*) AS programadas,
            SUM(
                CASE
                    WHEN v.id IS NULL THEN 1
                    ELSE 0
                END
            ) AS desviadas
        FROM lineas_dia ld
        LEFT JOIN viajes v
          ON v.fecha = ld.fecha
         AND v.id_chofer = ld.id_chofer
        WHERE ld.fecha BETWEEN ? AND ?
        GROUP BY ld.fecha
        ORDER BY ld.fecha
    """, (lunes.isoformat(), domingo.isoformat()))

    rows = cur.fetchall()

    return [
        {
            "fecha": r["fecha"],
            "programadas": r["programadas"],
            "ejecutadas": r["programadas"] - r["desviadas"],
            "desviadas": r["desviadas"],
        }
        for r in rows
    ]
