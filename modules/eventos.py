# modules/eventos.py

from datetime import datetime


# =================================================
# TABLA EVENTOS
# =================================================
def crear_tabla_eventos(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id_evento     INTEGER PRIMARY KEY AUTOINCREMENT,
            viaje_id      TEXT NOT NULL,
            tipo          TEXT NOT NULL,
            descripcion   TEXT,
            inicio        TEXT NOT NULL,
            fin           TEXT,
            creado_por    TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (viaje_id) REFERENCES viajes(id_viaje)
        );
    """)
    conn.commit()


# =================================================
# VIAJES CONFIRMADOS
# =================================================
def listar_viajes_confirmados(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.id_viaje,
            v.fecha,
            v.estado,
            ch.nombre  AS chofer,
            m.material AS material
        FROM viajes v
        LEFT JOIN choferes ch  ON ch.id_chofer = v.chofer_id
        LEFT JOIN materiales m ON m.id_material = v.material_id
        WHERE v.estado = 'CONFIRMADO'
        ORDER BY v.fecha DESC
    """)

    return cur.fetchall()


# =================================================
# CREAR EVENTO
# =================================================
def crear_evento(
    conn,
    viaje_id: str,
    tipo: str,
    descripcion: str,
    inicio,
    fin,
    usuario: str
):
    crear_tabla_eventos(conn)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO eventos (
            viaje_id,
            tipo,
            descripcion,
            inicio,
            fin,
            creado_por
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        viaje_id,
        tipo,
        descripcion,
        inicio.isoformat() if hasattr(inicio, "isoformat") else inicio,
        fin.isoformat() if fin and hasattr(fin, "isoformat") else fin,
        usuario
    ))

    conn.commit()


# =================================================
# LISTAR EVENTOS DE UN VIAJE
# =================================================
def listar_eventos_viaje(conn, viaje_id: str):
    crear_tabla_eventos(conn)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id_evento,
            tipo,
            descripcion,
            inicio,
            fin,
            creado_por
        FROM eventos
        WHERE viaje_id = ?
        ORDER BY inicio
    """, (viaje_id,))

    return cur.fetchall()
