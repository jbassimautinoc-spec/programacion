def init_db(conn):
    cur = conn.cursor()

    # =========================
    # PROGRAMACIÓN SEMANAL
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

    # =========================
    # DÍA OPERATIVO (LÍNEAS)
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lineas_dia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        id_chofer TEXT,
        id_tractor TEXT,
        id_material TEXT,
        origen_linea TEXT,   -- PROGRAMACION | FUERA_DE_PLAN
        estado TEXT,         -- PENDIENTE | CONFIRMADO | CANCELADO
        creado_por TEXT
    )
    """)

    # =========================
    # VIAJES CONFIRMADOS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS viajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linea_id INTEGER,
        fecha TEXT,
        id_chofer TEXT,
        id_tractor TEXT,
        id_material TEXT,
        id_cliente TEXT,
        id_origen TEXT,
        id_destino TEXT,
        origen_viaje TEXT,   -- PROGRAMACION | FUERA_DE_PLAN
        estado TEXT,
        creado_por TEXT
    )
    """)

    # =========================
    # EVENTOS DE VIAJE
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_viaje (
    id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
    viaje_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    inicio_ts TIMESTAMP NOT NULL,
    fin_ts TIMESTAMP NOT NULL,
    observacion TEXT,
    creado_por TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (viaje_id) REFERENCES viajes(id_viaje)
);
    """)

    # =========================
    # EVENTOS DE RECURSOS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_recursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,            -- FRANCO | TALLER
        sub_tipo TEXT,
        id_chofer TEXT,
        id_tractor TEXT,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        creado_por TEXT
    )
    """)
    

    conn.commit()
    
        # =========================
    # MAESTRO DE CHOFERES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS choferes (
        id_chofer TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        id_tractor TEXT,
        activo INTEGER DEFAULT 1
    )
    """)

    # =========================
    # ESTADO DEL TRACTOR
    # =========================
    cur = conn.cursor()
    try:
        cur.execute("""
    ALTER TABLE tractores
    ADD COLUMN estado TEXT DEFAULT 'OPERATIVO'
    """)
    except Exception:
        pass
    
    cur = conn.cursor()
    try:
        cur.execute("""
    ALTER TABLE choferes
    ADD COLUMN id_tractor TEXT
    """)
    except Exception:
     pass

    try:
        cur.execute("""
        ALTER TABLE tractores
        ADD COLUMN estado TEXT DEFAULT 'OPERATIVO'
        """)
    except Exception:
        # La columna ya existe
        pass
    
    conn.commit()
    # =========================
    
    