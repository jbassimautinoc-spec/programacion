from __future__ import annotations

from datetime import date, timedelta, datetime
from typing import Optional

from services.eventos_recursos import chofer_en_franco


# =================================================
# Helpers semana
# =================================================
def _lunes_de_semana(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _domingo_de_semana(d: date) -> date:
    return _lunes_de_semana(d) + timedelta(days=6)


def _codigo_semana(d) -> str:
    if isinstance(d, datetime):
        d = d.date()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


# =================================================
# Helpers materiales (evita adivinar "nombre")
# =================================================
def _material_display_col(conn) -> Optional[str]:
    """
    Devuelve el nombre de columna 'visible' en la tabla materiales.
    Evita errores tipo 'no such column: m.nombre' cuando el esquema usa
    'descripcion', 'material', etc.
    """
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(materiales)")
        cols = [r[1] for r in cur.fetchall()]  # r[1] = nombre columna
    except Exception:
        return None

    # Orden de preferencia (ajustado a esquemas típicos)
    preferred = [
        "nombre",
        "descripcion",
        "material",
        "nombre_material",
        "desc",
        "detalle",
    ]
    for c in preferred:
        if c in cols:
            return c
    return None


# =================================================
# STUB RRHH
# =================================================
def chofer_no_operativo_rrhh(conn, chofer_id: str, fecha: date) -> bool:
    return False


# =================================================
# CREAR LÍNEA EN lineas_dia (PROGRAMACIÓN)
# =================================================
def crear_linea_programada(
    conn,
    fecha: date,
    chofer_id: str,
    material_id: str,
    usuario: str
) -> bool:
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM lineas_dia
        WHERE fecha = ?
          AND id_chofer = ?
          AND origen_linea = 'PROGRAMACION'
    """, (fecha.isoformat(), chofer_id))

    if cur.fetchone():
        return False

    cur.execute("""
        INSERT INTO lineas_dia (
            fecha,
            id_chofer,
            id_material,
            estado,
            origen_linea,
            creado_por
        )
        VALUES (?, ?, ?, 'PENDIENTE', 'PROGRAMACION', ?)
    """, (
        fecha.isoformat(),
        chofer_id,
        material_id,
        usuario
    ))

    return True


# =================================================
# GENERAR PROGRAMACIÓN SEMANAL
# =================================================
def generar_programacion_semanal(
    conn,
    fecha_desde: date,
    choferes_ids: list[str],
    dias: list[str],
    material_id: str,
    usuario: str
):
    lunes = _lunes_de_semana(fecha_desde)

    mapa_dias = {
        "Lunes": 0,
        "Martes": 1,
        "Miércoles": 2,
        "Jueves": 3,
        "Viernes": 4,
        "Sábado": 5,
        "Domingo": 6,
    }

    resultado = {
        "creadas": 0,
        "omitidas": 0,
        "por_material": {},
        "mensajes": [],
    }

    for chofer_id in choferes_ids:
        for dia in dias:
            if dia not in mapa_dias:
                continue

            fecha_prog = lunes + timedelta(days=mapa_dias[dia])

            if chofer_en_franco(conn, chofer_id, fecha_prog):
                resultado["omitidas"] += 1
                resultado["mensajes"].append(
                    f"{fecha_prog} – Chofer {chofer_id}: FRANCO"
                )
                continue

            if chofer_no_operativo_rrhh(conn, chofer_id, fecha_prog):
                resultado["omitidas"] += 1
                resultado["mensajes"].append(
                    f"{fecha_prog} – Chofer {chofer_id}: RRHH"
                )
                continue

            if crear_linea_programada(
                conn,
                fecha_prog,
                chofer_id,
                material_id,
                usuario
            ):
                resultado["creadas"] += 1
                resultado["por_material"][material_id] = (
                    resultado["por_material"].get(material_id, 0) + 1
                )
            else:
                resultado["omitidas"] += 1
                resultado["mensajes"].append(
                    f"{fecha_prog} – Chofer {chofer_id}: YA EXISTE"
                )

    conn.commit()
    return resultado


# =================================================
# LISTADOS PARA UI
# =================================================
def listar_programacion_semana(conn, fecha_base: date):
    lunes = _lunes_de_semana(fecha_base)
    domingo = _domingo_de_semana(fecha_base)

    mat_col = _material_display_col(conn)

    cur = conn.cursor()

    # Si encontramos una columna "visible" en materiales, la usamos.
    # Si no, devolvemos el id_material también como "material" para no romper la UI.
    if mat_col:
        cur.execute(f"""
            SELECT
                l.id,
                l.fecha,
                ch.nombre AS chofer,
                l.id_material,
                m.{mat_col} AS material,
                l.estado
            FROM lineas_dia l
            LEFT JOIN choferes ch
                   ON ch.id_chofer = l.id_chofer
            LEFT JOIN materiales m
                   ON m.id_material = l.id_material
            WHERE l.fecha BETWEEN ? AND ?
              AND l.origen_linea = 'PROGRAMACION'
            ORDER BY l.fecha, ch.nombre
        """, (lunes.isoformat(), domingo.isoformat()))
    else:
        cur.execute("""
            SELECT
                l.id,
                l.fecha,
                ch.nombre AS chofer,
                l.id_material,
                l.id_material AS material,
                l.estado
            FROM lineas_dia l
            LEFT JOIN choferes ch
                   ON ch.id_chofer = l.id_chofer
            WHERE l.fecha BETWEEN ? AND ?
              AND l.origen_linea = 'PROGRAMACION'
            ORDER BY l.fecha, ch.nombre
        """, (lunes.isoformat(), domingo.isoformat()))

    return cur.fetchall()


def listar_programacion_por_programacion(conn, fecha_base: date):
    return listar_programacion_semana(conn, fecha_base)


def contadores_semana(conn, fecha_base: date):
    lunes = _lunes_de_semana(fecha_base)
    domingo = _domingo_de_semana(fecha_base)

    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT id_chofer) AS choferes_programados
        FROM lineas_dia
        WHERE fecha BETWEEN ? AND ?
          AND origen_linea = 'PROGRAMACION'
    """, (lunes.isoformat(), domingo.isoformat()))

    r = cur.fetchone()

    return {
        "total": r[0] or 0,
        "arena": 0,
        "piedra": 0,
        "choferes_programados": r[1] or 0,
    }


# =================================================
# ELIMINAR LÍNEA PROGRAMADA
# =================================================
def eliminar_linea_programacion(conn, id_linea: int) -> bool:
    cur = conn.cursor()

    cur.execute("""
        SELECT estado
        FROM lineas_dia
        WHERE id = ?
          AND origen_linea = 'PROGRAMACION'
    """, (id_linea,))

    row = cur.fetchone()
    if not row:
        return False

    if row[0] == "CONFIRMADO":
        return False

    cur.execute("""
        DELETE FROM lineas_dia
        WHERE id = ?
          AND origen_linea = 'PROGRAMACION'
    """, (id_linea,))

    conn.commit()
    return cur.rowcount > 0
