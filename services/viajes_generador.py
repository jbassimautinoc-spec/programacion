# services/viajes_generador.py

from services.viajes import crear_viaje


def generar_viaje_desde_linea(conn, id_linea, creado_por=None):
    cur = conn.cursor()

    # 1) Traer la línea programada
    cur.execute("""
        SELECT
            l.id_linea,
            l.fecha,
            l.chofer_id,
            l.material,
            l.id_programacion,
            l.viaje_generado,
            p.confirmada
        FROM lineas_programadas l
        JOIN programaciones p ON p.id_programacion = l.id_programacion
        WHERE l.id_linea = ?
    """, (id_linea,))

    row = cur.fetchone()
    if not row:
        raise ValueError("La línea programada no existe")

    (
        id_linea_db,
        fecha,
        chofer_id,
        material,
        id_programacion,
        viaje_generado,
        programacion_confirmada
    ) = row

    # 2) Validaciones duras
    if not programacion_confirmada:
        raise ValueError("La programación no tiene foto confirmada")

    if viaje_generado:
        raise ValueError("Esta línea ya generó un viaje")

    # 3) Crear el viaje (persistencia inmediata)
    id_viaje = crear_viaje(
        conn=conn,
        fecha=fecha,
        material=material,
        origen="",     # se completa luego por plantilla o edición
        destino="",    # idem
        estado="PROGRAMADO",
        origen_viaje="programacion",
        chofer_id=chofer_id,
        id_programacion=id_programacion,
        id_linea_programada=id_linea_db,
        creado_por=creado_por
    )

    # 4) Marcar la línea como ejecutada
    cur.execute("""
        UPDATE lineas_programadas
        SET viaje_generado = 1
        WHERE id_linea = ?
    """, (id_linea_db,))

    conn.commit()

    return id_viaje
