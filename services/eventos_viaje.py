# services/eventos_viaje.py

from __future__ import annotations
from datetime import datetime

# =================================================
# VALIDACIÓN CENTRAL
# =================================================

def _validar_viaje_no_finalizado(conn, viaje_id):
    """
    Impide cargar eventos en viajes FINALIZADOS.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT estado FROM viajes WHERE id = ?",
        (viaje_id,)
    )
    row = cur.fetchone()
    if row and row["estado"] == "FINALIZADO":
        raise ValueError("No se pueden cargar eventos en un viaje FINALIZADO")


# =================================================
# HELPERS
# =================================================

def duracion_evento_min(inicio_ts, fin_ts) -> int:
    return int((fin_ts - inicio_ts).total_seconds() // 60)


# =================================================
# EVENTOS GENÉRICOS DE VIAJE
# =================================================

def crear_evento_viaje(
    conn,
    viaje_id,
    tipo,
    inicio_ts,
    fin_ts,
    observacion,
    usuario
):
    _validar_viaje_no_finalizado(conn, viaje_id)

    if fin_ts <= inicio_ts:
        raise ValueError("La fecha/hora fin debe ser posterior al inicio")

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO eventos_viaje (
            viaje_id,
            tipo,
            inicio_ts,
            fin_ts,
            observacion,
            creado_por
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        viaje_id,
        tipo,
        inicio_ts,
        fin_ts,
        observacion,
        usuario
    ))

    conn.commit()
    return cur.lastrowid


def listar_eventos_viaje(conn, viaje_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id_evento,
            tipo,
            inicio_ts,
            fin_ts,
            observacion,
            creado_por,
            creado_en
        FROM eventos_viaje
        WHERE viaje_id = ?
        ORDER BY inicio_ts
    """, (viaje_id,))
    rows = cur.fetchall()

    eventos = []
    for r in rows:
        d = dict(r)

        inicio = d.get("inicio_ts")
        fin = d.get("fin_ts")

        inicio_dt = datetime.fromisoformat(inicio) if isinstance(inicio, str) else inicio
        fin_dt = datetime.fromisoformat(fin) if isinstance(fin, str) else fin

        d["duracion_min"] = (
            duracion_evento_min(inicio_dt, fin_dt)
            if inicio_dt and fin_dt else 0
        )
        eventos.append(d)

    return eventos


# =================================================
# EVENTOS DE DEMORA
# =================================================

TIPOS_DEMORA = {
    "DEMORA_CARGA",
    "DEMORA_DESCARGA",
    "DEMORA_CHOFER"
}


def crear_evento_demora(
    conn,
    viaje_id,
    tipo,
    inicio_ts,
    fin_ts,
    observacion,
    usuario
):
    _validar_viaje_no_finalizado(conn, viaje_id)

    if tipo not in TIPOS_DEMORA:
        raise ValueError("Tipo de demora inválido")

    if fin_ts <= inicio_ts:
        raise ValueError("La fecha/hora fin debe ser posterior al inicio")

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO eventos_viaje (
            viaje_id,
            tipo,
            inicio_ts,
            fin_ts,
            observacion,
            creado_por
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        viaje_id,
        tipo,
        inicio_ts,
        fin_ts,
        observacion,
        usuario
    ))
    conn.commit()
    return cur.lastrowid


def listar_demoras_viaje(conn, viaje_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id_evento,
            tipo,
            inicio_ts,
            fin_ts,
            observacion,
            creado_en
        FROM eventos_viaje
        WHERE viaje_id = ?
          AND tipo IN ('DEMORA_CARGA', 'DEMORA_DESCARGA', 'DEMORA_CHOFER')
        ORDER BY inicio_ts
    """, (viaje_id,))
    rows = cur.fetchall()

    demoras = []
    for r in rows:
        d = dict(r)

        inicio = d.get("inicio_ts")
        fin = d.get("fin_ts")

        inicio_dt = datetime.fromisoformat(inicio) if isinstance(inicio, str) else inicio
        fin_dt = datetime.fromisoformat(fin) if isinstance(fin, str) else fin

        d["duracion_min"] = (
            duracion_evento_min(inicio_dt, fin_dt)
            if inicio_dt and fin_dt else 0
        )
        demoras.append(d)

    return demoras


def duracion_demoras_viaje(conn, viaje_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            tipo,
            SUM(
                (JULIANDAY(fin_ts) - JULIANDAY(inicio_ts)) * 24 * 60
            ) AS minutos
        FROM eventos_viaje
        WHERE viaje_id = ?
          AND tipo IN ('DEMORA_CARGA', 'DEMORA_DESCARGA', 'DEMORA_CHOFER')
        GROUP BY tipo
    """, (viaje_id,))

    return {
        r["tipo"]: int(r["minutos"] or 0)
        for r in cur.fetchall()
    }
