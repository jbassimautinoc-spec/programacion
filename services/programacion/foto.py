# services/programacion/foto.py

from datetime import datetime


def confirmar_programacion(conn, semana: str, usuario: str):
    cur = conn.cursor()

    # -------------------------------------------------
    # 1. Buscar programación semanal
    # -------------------------------------------------
    cur.execute("""
        SELECT id_programacion, estado
        FROM programacion_semanal
        WHERE semana = ?
    """, (semana,))
    row = cur.fetchone()

    if not row:
        raise ValueError("No existe programación para esa semana")

    id_programacion, estado = row

    if estado == "CONFIRMADA":
        raise ValueError("La programación ya está confirmada")

    # -------------------------------------------------
    # 2. Validar que tenga líneas
    # -------------------------------------------------
    cur.execute("""
        SELECT COUNT(*)
        FROM programacion_diaria
        WHERE id_programacion = ?
    """, (id_programacion,))
    if cur.fetchone()[0] == 0:
        raise ValueError("No se puede confirmar una programación sin líneas")

    # -------------------------------------------------
    # 3. Confirmar la programación (foto)
    # -------------------------------------------------
    cur.execute("""
        UPDATE programacion_semanal
        SET
            estado = 'CONFIRMADA',
            confirmada_por = ?,
            confirmada_at = ?
        WHERE id_programacion = ?
    """, (
        usuario,
        datetime.now().isoformat(),
        id_programacion
    ))

    # -------------------------------------------------
    # 4. Generar DÍA OPERATIVO desde la programación
    # -------------------------------------------------
    cur.execute("""
        INSERT INTO lineas_dia (
            fecha,
            chofer_id,
            material_id,
            estado,
            origen_linea
        )
        SELECT
            fecha,
            chofer_id,
            material_id,
            'PENDIENTE',
            'PLAN'
        FROM programacion_diaria
        WHERE id_programacion = ?
    """, (id_programacion,))

    conn.commit()

    return {
        "ok": True,
        "lineas_generadas": cur.rowcount
    }
