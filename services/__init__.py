# services/db_init.py
import sqlite3


def init_db(conn: sqlite3.Connection):
    cur = conn.cursor()

    # =========================
    # MAESTROS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS choferes (
        id_chofer TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        activo INTEGER DEFAULT 1,
        tipo_flota TEXT DEFAULT 'PROPIA',
        id_tractor TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tractores (
        id_tractor TEXT PRIMARY KEY,
        patente TEXT NOT NULL,
        activo INTEGER DEFAULT 1,
        tipo_flota TEXT DEFAULT 'PROPIA',
        estado TEXT DEFAULT 'OPERATIVO'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS materiales (
        id_material TEXT PRIMARY KEY,
        material TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente TEXT PRIMARY KEY,
        cliente TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS origenes (
        id_origen TEXT PRIMARY KEY,
        origen TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS destinos (
        id_destino TEXT PRIMARY KEY,
        destino TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)

    # =========================
    # PROGRAMACIÓN
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS programacion_semanal (
        id_programacion TEXT PRIMARY KEY,
        semana TEXT NOT NULL,
        estado TEXT NOT NULL,
        creado_por TEXT,
        creado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS programacion_diaria (
        id_programacion TEXT,
        fecha TEXT,
        id_linea TEXT,
        PRIMARY KEY (id_programacion, fecha, id_linea)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS lineas_dia (
        id_linea TEXT PRIMARY KEY,
        fecha TEXT,
        estado TEXT,
        chofer_id TEXT,
        tractor_id TEXT,
        material_id TEXT,
        origen_linea TEXT,
        creado_por TEXT
    )
    """)

    # =========================
    # VIAJES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS viajes (
        id_viaje TEXT PRIMARY KEY,
        fecha TEXT,
        estado TEXT,
        chofer_id TEXT,
        tractor_id TEXT,
        material_id TEXT,
        origen_id TEXT,
        destino_id TEXT,
        id_linea TEXT,
        creado_por TEXT
    )
    """)

    # =========================
    # EVENTOS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_recursos (
        id_evento TEXT PRIMARY KEY,
        tipo TEXT,
        chofer_id TEXT,
        tractor_id TEXT,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        observacion TEXT,
        creado_por TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_viaje (
        id_evento TEXT PRIMARY KEY,
        id_viaje TEXT,
        tipo TEXT,
        duracion_min INTEGER,
        observacion TEXT,
        creado_por TEXT,
        creado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
