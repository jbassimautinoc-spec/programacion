def asignar_tractor_preferente(conn, id_chofer, id_tractor):
    cur = conn.cursor()

    # desactivar vínculos previos
    cur.execute("""
        UPDATE chofer_tractor
        SET activo = 0
        WHERE id_chofer = ?
    """, (id_chofer,))

    # insertar nuevo vínculo
    cur.execute("""
        INSERT INTO chofer_tractor (id_chofer, id_tractor, preferente, activo)
        VALUES (?, ?, 1, 1)
    """, (id_chofer, id_tractor))

    conn.commit()


def obtener_tractor_preferente(conn, id_chofer):
    cur = conn.cursor()
    cur.execute("""
        SELECT id_tractor
        FROM chofer_tractor
        WHERE id_chofer = ?
          AND preferente = 1
          AND activo = 1
        LIMIT 1
    """, (id_chofer,))
    row = cur.fetchone()
    return row["id_tractor"] if row else None
