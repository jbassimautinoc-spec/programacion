from datetime import date, timedelta


def semana_de_fecha(fecha: date) -> str:
    y, w, _ = fecha.isocalendar()
    return f"{y}-W{w:02d}"


def generar_programacion_semanal(
    conn,
    semana: str,
    choferes: list[int],
    dias: list[int],
    material_id: int,
    usuario: str
):
    """
    Genera líneas PLANIFICADAS para una semana.
    No crea viajes. No ejecuta.
    """
    cur = conn.cursor()

    year = int(semana.split("-W")[0])
    week = int(semana.split("-W")[1])

    for chofer_id in choferes:
        for d in dias:
            fecha = date.fromisocalendar(year, week, d + 1)

            cur.execute("""
                INSERT INTO programacion_semanal (
                    semana,
                    fecha,
                    chofer_id,
                    material_id,
                    creado_por
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                semana,
                fecha.isoformat(),
                chofer_id,
                material_id,
                usuario
            ))

    conn.commit()


def listar_programacion_semana(conn, semana: str):
    """
    Devuelve la programación semanal (solo lectura)
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT
            p.id,
            p.semana,
            p.fecha,
            ch.nombre AS chofer,
            m.material
        FROM programacion_semanal p
        JOIN choferes ch ON ch.id_chofer = p.chofer_id
        JOIN materiales m ON m.id_material = p.material_id
        WHERE p.semana = ?
        ORDER BY p.fecha, ch.nombre
    """, (semana,))
    return [dict(r) for r in cur.fetchall()]


def derivar_lineas_dia(conn, fecha: date, usuario: str):
    """
    Baja las líneas del PLAN semanal al día operativo.
    Se ejecuta una sola vez por día.
    """
    semana = semana_de_fecha(fecha)
    cur = conn.cursor()

    # Evitar duplicar
    cur.execute("""
        SELECT COUNT(*) FROM lineas_dia WHERE fecha = ?
    """, (fecha.isoformat(),))

    if cur.fetchone()[0] > 0:
        return

    cur.execute("""
        INSERT INTO lineas_dia (
            fecha,
            chofer_id,
            material_id,
            origen_linea,
            estado,
            creado_por
        )
        SELECT
            p.fecha,
            p.chofer_id,
            p.material_id,
            'PROGRAMACION',
            'PENDIENTE',
            ?
        FROM programacion_semanal p
        WHERE p.fecha = ?
    """, (usuario, fecha.isoformat()))

    conn.commit()
