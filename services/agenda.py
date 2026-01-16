from datetime import datetime, date
from typing import List, Dict
import sqlite3

# -------------------------------------------------
# Helper: SOLO ISO (YYYY-MM-DD)
# -------------------------------------------------
def _parse_fecha(valor) -> date | None:
    if not valor:
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    s = str(valor).strip()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


# -------------------------------------------------
# Service principal
# -------------------------------------------------
def listar_viajes_agenda(conn, fecha_desde: date, fecha_hasta: date) -> List[Dict]:
    """
    Devuelve items unificados para la Agenda:
    - LINEA  -> programación diaria (lineas_dia)
    - VIAJE  -> operación (viajes)
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    items: List[Dict] = []

    # =========================
    # LÍNEAS (programación)
    # =========================
    cur.execute("""
        SELECT
            fecha,
            id_chofer,
            id_material,
            estado
        FROM lineas_dia
        WHERE fecha IS NOT NULL
        ORDER BY fecha
    """)
    for r in cur.fetchall():
        fecha = _parse_fecha(r["fecha"])
        if not fecha:
            continue
        if not (fecha_desde <= fecha <= fecha_hasta):
            continue

        items.append({
            "tipo": "LINEA",
            "fecha": fecha,
            "estado": (r["estado"] or "").strip().upper(),
            "chofer": r["id_chofer"],
            "material": r["id_material"],
        })

    # =========================
    # VIAJES (ejecución)
    # =========================
    cur.execute("""
        SELECT
            fecha,
            id_chofer,
            id_material,
            estado
        FROM viajes
        WHERE fecha IS NOT NULL
        ORDER BY fecha
    """)
    for r in cur.fetchall():
        fecha = _parse_fecha(r["fecha"])
        if not fecha:
            continue
        if not (fecha_desde <= fecha <= fecha_hasta):
            continue

        items.append({
            "tipo": "VIAJE",
            "fecha": fecha,
            "estado": (r["estado"] or "").strip().upper(),
            "chofer": r["id_chofer"],
            "material": r["id_material"],
        })

    return items
