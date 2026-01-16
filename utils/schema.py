def init_db(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # =========================
    # MAESTROS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS choferes (
        id_chofer TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        transporte TEXT,
        activo INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tractores (
        id_tractor TEXT PRIMARY KEY,
        patente TEXT NOT NULL,
        transporte TEXT,
        activo INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS materiales (
        id_material TEXT PRIMARY KEY,
        material TEXT NOT NULL UNIQUE,
        activo INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente TEXT PRIMARY KEY,
        cliente TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS origenes (
        id_origen TEXT PRIMARY KEY,
        origen TEXT NOT NULL UNIQUE,
        activo INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS destinos (
        id_destino TEXT PRIMARY KEY,
        destino TEXT NOT NULL UNIQUE,
        activo INTEGER NOT NULL DEFAULT 1
    );
    """)

    # =========================
    # PLANTILLAS DE VIAJE
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS plantillas_viaje (
        id_plantilla TEXT PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE,
        material_id TEXT NOT NULL,
        cliente_id TEXT NOT NULL,
        origen_id TEXT NOT NULL,
        destino_id TEXT NOT NULL,
        observacion TEXT,
        activo INTEGER NOT NULL DEFAULT 1,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (material_id) REFERENCES materiales(id_material),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente),
        FOREIGN KEY (origen_id) REFERENCES origenes(id_origen),
        FOREIGN KEY (destino_id) REFERENCES destinos(id_destino)
    );
    """)

    # =========================
    # VIAJES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS viajes (
        id_viaje TEXT PRIMARY KEY,
        nro_viaje INTEGER UNIQUE,
        fecha TEXT NOT NULL,

        chofer_id TEXT,
        tractor_id TEXT,
        cliente_id TEXT,
        material_id TEXT,
        origen_id TEXT,
        destino_id TEXT,
        id_plantilla TEXT,

        estado TEXT NOT NULL DEFAULT 'CONFIRMADO',

        FOREIGN KEY (chofer_id) REFERENCES choferes(id_chofer),
        FOREIGN KEY (tractor_id) REFERENCES tractores(id_tractor),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente),
        FOREIGN KEY (material_id) REFERENCES materiales(id_material),
        FOREIGN KEY (origen_id) REFERENCES origenes(id_origen),
        FOREIGN KEY (destino_id) REFERENCES destinos(id_destino),
        FOREIGN KEY (id_plantilla) REFERENCES plantillas_viaje(id_plantilla)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_viajes_fecha ON viajes(fecha);")

    # =========================
    # EVENTOS DE VIAJE (DEMORAS)
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_viaje (
    id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
    viaje_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    inicio_ts TEXT NOT NULL,
    fin_ts TEXT NOT NULL,
    observacion TEXT,
    creado_por TEXT,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

    """)

    # =========================
    # EVENTOS DE RECURSOS (FRANCO / TALLER)
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_recursos (
        id_evento TEXT PRIMARY KEY,
        tipo TEXT NOT NULL,
        chofer_id TEXT,
        tractor_id TEXT,
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NOT NULL,
        observacion TEXT,
        creado_por TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (chofer_id) REFERENCES choferes(id_chofer),
        FOREIGN KEY (tractor_id) REFERENCES tractores(id_tractor)
    );
    """)

    # =========================
    # PROGRAMACIÓN
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS programacion_semanal (
        id_programacion INTEGER PRIMARY KEY AUTOINCREMENT,
        semana TEXT NOT NULL UNIQUE,
        estado TEXT NOT NULL DEFAULT 'BORRADOR',
        confirmada_por TEXT,
        confirmada_at TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS programacion_diaria (
        id_linea INTEGER PRIMARY KEY AUTOINCREMENT,
        id_programacion INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        chofer_id TEXT NOT NULL,
        material_id TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'PROGRAMADO',

        FOREIGN KEY (id_programacion) REFERENCES programacion_semanal(id_programacion),
        FOREIGN KEY (chofer_id) REFERENCES choferes(id_chofer),
        FOREIGN KEY (material_id) REFERENCES materiales(id_material)
    );
    """)

    # =========================
    # DÍA OPERATIVO
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lineas_dia (
        id_linea INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        chofer_id TEXT,
        tractor_id TEXT,
        material_id TEXT,
        estado TEXT NOT NULL DEFAULT 'PENDIENTE',
        origen_linea TEXT NOT NULL DEFAULT 'FUERA_DE_PLAN',

        FOREIGN KEY (chofer_id) REFERENCES choferes(id_chofer),
        FOREIGN KEY (tractor_id) REFERENCES tractores(id_tractor),
        FOREIGN KEY (material_id) REFERENCES materiales(id_material)
    );
    """)

    conn.commit()
def init_db(conn):
    cur = conn.cursor()

    # =========================
    # TABLAS (las que ya tengas)
    # =========================
    # ... tus CREATE TABLE ...

    # =========================
    # MIGRACIONES OBLIGATORIAS
    # =========================

    # 1️⃣ estado en tractores
    try:
        cur.execute("""
        ALTER TABLE tractores
        ADD COLUMN estado TEXT DEFAULT 'OPERATIVO'
        """)
    except Exception:
        pass

    # 2️⃣ id_tractor en choferes
    try:
        cur.execute("""
        ALTER TABLE choferes
        ADD COLUMN id_tractor TEXT
        """)
    except Exception:
        pass
    # =========================
    # MIGRACIÓN: creado_por en programacion_semanal
    # =========================
    try:
        cur.execute("""
        ALTER TABLE programacion_semanal
        ADD COLUMN creado_por TEXT
        """)
    except Exception:
        pass
    
    conn.commit()
    

