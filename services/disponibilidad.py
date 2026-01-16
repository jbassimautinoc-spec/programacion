from datetime import date, timedelta

from services.eventos import (
    chofer_disponible,
    tractor_disponible,
    motivo_chofer_no_disponible,
    motivo_tractor_no_disponible,
)

# =================================================
# CONTADORES DE CHOFERES (SEMANALES)
# =================================================

def contadores_choferes(conn, fecha):
    cur = conn.cursor()
    cur.execute("SELECT id_chofer FROM choferes WHERE activo = 1")
    choferes = [r["id_chofer"] for r in cur.fetchall()]

    disponibles = set()
    no_disponibles = 0
    motivos = {}

    for cid in choferes:
        if chofer_disponible(conn, cid, fecha):
            disponibles.add(cid)
        else:
            no_disponibles += 1
            motivo = motivo_chofer_no_disponible(conn, cid, fecha)
            if motivo:
                motivos[motivo] = motivos.get(motivo, 0) + 1

    lunes = fecha
    domingo = fecha + timedelta(days=6)

    cur.execute(
        "SELECT DISTINCT id_chofer "
        "FROM lineas_dia "
        "WHERE fecha BETWEEN ? AND ? "
        "AND origen_linea = 'PROGRAMACION' "
        "AND estado != 'CANCELADO'",
        (lunes.isoformat(), domingo.isoformat()),
    )

    choferes_programados = {r["id_chofer"] for r in cur.fetchall()}
    pendientes = disponibles - choferes_programados

    return {
        "total": len(choferes),
        "disponibles": len(disponibles),
        "no_disponibles": no_disponibles,
        "pendientes_programar": len(pendientes),
        "motivos": motivos,
    }


# =================================================
# CONTADORES DE TRACTORES (SEMANALES)
# =================================================

def contadores_tractores(conn, fecha):
    cur = conn.cursor()
    cur.execute("SELECT id_tractor FROM tractores WHERE activo = 1")
    tractores = cur.fetchall()

    disponibles = 0
    no_disponibles = 0

    for t in tractores:
        tid = t["id_tractor"]
        if tractor_disponible(conn, tid, fecha):
            disponibles += 1
        else:
            no_disponibles += 1

    return {
        "total": len(tractores),
        "disponibles": disponibles,
        "no_disponibles": no_disponibles,
    }


# =================================================
# TRACTORES SUELTOS
# =================================================

def listar_tractores_sueltos(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT t.id_tractor, t.patente, t.estado "
        "FROM tractores t "
        "LEFT JOIN choferes c ON c.id_tractor = t.id_tractor "
        "WHERE c.id_chofer IS NULL "
        "AND t.activo = 1 "
        "AND t.estado = 'OPERATIVO'"
    )
    return [dict(r) for r in cur.fetchall()]


# =================================================
# POOL DISPONIBILIDAD DIARIA (DÍA OPERATIVO)
# =================================================

def pool_disponibilidad_diaria(conn, fecha: date):
    cur = conn.cursor()

    # Choferes
    cur.execute("SELECT id_chofer FROM choferes WHERE activo = 1")
    choferes = [r["id_chofer"] for r in cur.fetchall()]

    choferes_disponibles = [
        cid for cid in choferes
        if chofer_disponible(conn, cid, fecha)
    ]

    # Tractores
    cur.execute("SELECT id_tractor FROM tractores WHERE activo = 1")
    tractores = [r["id_tractor"] for r in cur.fetchall()]

    tractores_disponibles = []
    tractores_mantenimiento = []

    for tid in tractores:
        if tractor_disponible(conn, tid, fecha):
            tractores_disponibles.append(tid)
        else:
            tractores_mantenimiento.append(tid)

    # Pool disponible = mínimo operativo real
    pool_disponible = min(
        len(choferes_disponibles),
        len(tractores_disponibles)
    )

    return {
        # métricas usadas por pages/2_dia_operativo.py
        "tractores_total": len(tractores),
        "tractores_mantenimiento": len(tractores_mantenimiento),
        "choferes_disponibles": len(choferes_disponibles),
        "pool_disponible": pool_disponible,

        # listas por si se usan en otro lado
        "choferes_disponibles_list": choferes_disponibles,
        "tractores_disponibles_list": tractores_disponibles,
    }
