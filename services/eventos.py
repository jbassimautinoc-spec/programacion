"""
services/eventos.py
Capa de reglas de disponibilidad de recursos.
Se apoya en eventos_recursos (FRANCO / TALLER)
y expone una API limpia para Programación.
"""

from datetime import date
from services.eventos_recursos import (
    chofer_en_franco,
    tractor_en_taller,
)

# =================================================
# DISPONIBILIDAD DE CHOFER
# =================================================

def chofer_disponible(conn, id_chofer: int, fecha: date) -> bool:
    if chofer_en_franco(conn, id_chofer, fecha):
        return False
    return True


def motivo_chofer_no_disponible(conn, id_chofer: int, fecha: date) -> str | None:
    if chofer_en_franco(conn, id_chofer, fecha):
        return "FRANCO"
    return None


# =================================================
# DISPONIBILIDAD DE TRACTOR
# =================================================

def tractor_disponible(conn, id_tractor: int, fecha: date) -> bool:
    if tractor_en_taller(conn, id_tractor, fecha):
        return False
    return True


def motivo_tractor_no_disponible(conn, id_tractor: int, fecha: date) -> str | None:
    if tractor_en_taller(conn, id_tractor, fecha):
        return "TALLER"
    return None


# =================================================
# DISPONIBILIDAD CONJUNTA
# =================================================

def recursos_disponibles(conn, id_chofer: int, id_tractor: int, fecha: date) -> dict:
    chofer_ok = chofer_disponible(conn, id_chofer, fecha)
    tractor_ok = tractor_disponible(conn, id_tractor, fecha)

    return {
        "chofer_disponible": chofer_ok,
        "tractor_disponible": tractor_ok,
        "motivo_chofer": None if chofer_ok else motivo_chofer_no_disponible(conn, id_chofer, fecha),
        "motivo_tractor": None if tractor_ok else motivo_tractor_no_disponible(conn, id_tractor, fecha),
        "disponible": chofer_ok and tractor_ok,
    }


# =================================================
# EVENTOS (LECTURA SIMPLE)
# =================================================

def listar_eventos(
    conn,
    desde=None,
    hasta=None,
    recurso_tipo=None,
    recurso_id=None,
    tipos=None,
):
    cur = conn.cursor()

    where = []
    params = []

    if desde:
        where.append("fecha_inicio >= ?")
        params.append(desde)

    if hasta:
        where.append("fecha_fin <= ?")
        params.append(hasta)

    if recurso_tipo:
        where.append("recurso_tipo = ?")
        params.append(recurso_tipo)

    if recurso_id:
        where.append("recurso_id = ?")
        params.append(recurso_id)

    if tipos:
        placeholders = ",".join("?" for _ in tipos)
        where.append(f"tipo IN ({placeholders})")
        params.extend(tipos)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    cur.execute(
        f"""
        SELECT *
        FROM eventos
        {where_sql}
        ORDER BY fecha_inicio DESC
        """,
        params,
    )

    return [dict(r) for r in cur.fetchall()]
