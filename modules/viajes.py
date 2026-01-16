# modules/viajes.py

from datetime import date


def listar_viajes(conn, fecha: date):
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.id_viaje      AS id_viaje,
            v.fecha,
            v.estado,

            ch.nombre       AS chofer,
            t.patente       AS tractor,
            m.material      AS material,
            c.cliente       AS cliente,
            o.origen        AS origen,
            d.destino       AS destino

        FROM viajes v
        LEFT JOIN choferes  ch ON ch.id_chofer  = v.chofer_id
        LEFT JOIN tractores t  ON t.id_tractor = v.tractor_id
        LEFT JOIN materiales m ON m.id_material = v.material_id
        LEFT JOIN clientes  c  ON c.id_cliente = v.cliente_id
        LEFT JOIN origenes  o  ON o.id_origen   = v.origen_id
        LEFT JOIN destinos  d  ON d.id_destino  = v.destino_id

        WHERE v.fecha = ?
        ORDER BY ch.nombre
    """, (fecha.isoformat(),))

    return cur.fetchall()

