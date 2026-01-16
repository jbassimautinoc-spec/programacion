from __future__ import annotations
from datetime import date


# =================================================
# Helpers - detectar esquema real
# =================================================
def _cols(conn, table: str) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}  # r[1] = nombre columna


def _eventos_ref_col(conn) -> str:
    """
    Devuelve el nombre de columna en eventos_recursos que referencia al tractor.
    Evita seguir adivinando (tractor_id / recurso_id / etc).

    Si no encuentra ninguna, levanta error con detalle.
    """
    c = _cols(conn, "eventos_recursos")

    # Nombres posibles (orden de preferencia)
    candidates = [
        "tractor_id",
        "id_tractor",
        "tractor",
        "recurso_id",
        "id_recurso",
        "recurso",
        "unidad_id",
        "id_unidad",
    ]
    for name in candidates:
        if name in c:
            return name

    raise RuntimeError(
        "No encuentro la columna que referencia al tractor en eventos_recursos. "
        f"Columnas disponibles: {sorted(c)}"
    )


def _has_col(conn, table: str, col: str) -> bool:
    return col in _cols(conn, table)


def _rows_to_dicts(cur, rows):
    # Si tu conexión usa sqlite3.Row, dict(row) funciona.
    # Si no, lo convertimos por descripción del cursor.
    try:
        return [dict(r) for r in rows]
    except Exception:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


# =================================================
# INICIAR MANTENIMIENTO CORRECTIVO
# =================================================
def iniciar_mantenimiento_correctivo(
    conn,
    tractor_id: str,
    fecha_inicio: date,
    fecha_fin: date | None,  # se ignora al iniciar
    usuario: str,
    observacion: str | None = None,
):
    """
    Flujo Taller:
    1) Desvincula chofer asociado (si lo hubiera)
    2) Inserta evento mantenimiento correctivo
    3) Cambia estado tractor a MANTENIMIENTO
    """

    cur = conn.cursor()
    ref_col = _eventos_ref_col(conn)
    cols = _cols(conn, "eventos_recursos")

    # 1️⃣ Desvincular chofer del tractor
    cur.execute("""
        UPDATE choferes
        SET id_tractor = NULL
        WHERE id_tractor = ?
    """, (tractor_id,))

    # 2️⃣ Insertar evento de mantenimiento (SIN fecha_fin)
    insert_cols = ["tipo", ref_col, "fecha_inicio"]
    insert_vals = ["MANTENIMIENTO_CORRECTIVO", tractor_id, fecha_inicio]

    # usuario creador (si existe)
    if "creado_por" in cols:
        insert_cols.append("creado_por")
        insert_vals.append(usuario)
    elif "usuario" in cols:
        insert_cols.append("usuario")
        insert_vals.append(usuario)
    elif "created_by" in cols:
        insert_cols.append("created_by")
        insert_vals.append(usuario)

    # observación (si existe la columna)
    if observacion and "observacion" in cols:
        insert_cols.append("observacion")
        insert_vals.append(observacion)

    placeholders = ",".join(["?"] * len(insert_cols))
    colnames = ",".join(insert_cols)

    cur.execute(
        f"""
        INSERT INTO eventos_recursos ({colnames})
        VALUES ({placeholders})
        """,
        tuple(insert_vals),
    )

    # 3️⃣ Cambiar estado tractor
    cur.execute("""
        UPDATE tractores
        SET estado = 'MANTENIMIENTO'
        WHERE id_tractor = ?
    """, (tractor_id,))

    conn.commit()


# =================================================
# FINALIZAR MANTENIMIENTO
# =================================================
def finalizar_mantenimiento(conn, evento_id: int, tractor_id: str):
    """
    Finaliza mantenimiento:
    - Cierra el evento (fecha_fin)
    - Devuelve tractor a estado OPERATIVO
    """
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE eventos_recursos
        SET fecha_fin = ?
        WHERE id = ?
          AND tipo = 'MANTENIMIENTO_CORRECTIVO'
        """,
        (date.today(), evento_id),
    )

    cur.execute(
        """
        UPDATE tractores
        SET estado = 'OPERATIVO'
        WHERE id_tractor = ?
        """,
        (tractor_id,),
    )

    conn.commit()


# =================================================
# LISTAR TRACTORES EN MANTENIMIENTO
# =================================================
def listar_tractores_en_mantenimiento(conn, solo_activos: bool = True):
    """
    Lista tractores en mantenimiento correctivo.
    Auto-detecta la columna FK en eventos_recursos para no romper por esquema.
    """
    cur = conn.cursor()
    ref_col = _eventos_ref_col(conn)

    where_activos = "AND e.fecha_fin IS NULL" if solo_activos else ""

    cur.execute(
        f"""
        SELECT
            t.id_tractor,
            t.patente,
            e.id AS evento_id,
            e.fecha_inicio,
            e.fecha_fin
        FROM eventos_recursos e
        JOIN tractores t
          ON t.id_tractor = e.{ref_col}
        WHERE e.tipo = 'MANTENIMIENTO_CORRECTIVO'
        {where_activos}
        ORDER BY e.fecha_inicio DESC
        """
    )

    rows = cur.fetchall()
    return _rows_to_dicts(cur, rows)
