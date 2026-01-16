import streamlit as st
from pathlib import Path
import sys


# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# -------------------------------------------------
# CONFIG GENERAL (UNA SOLA VEZ)
# -------------------------------------------------
st.set_page_config(
    page_title="Programación y Monitoreo BCA",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------
# DB (UNA SOLA VEZ) + INIT DB (OBLIGATORIO)
# -------------------------------------------------
from utils.db import get_connection
from services.db_init import init_db  # <-- este archivo debe existir

conn = get_connection()
init_db(conn)  # <-- crea TODAS las tablas antes de importar Excel



# -------------------------------------------------
# USUARIOS Y ROLES (SIMPLE Y EFECTIVO)
# -------------------------------------------------
USERS = {
    "jbassi@grupobca.com.ar": "Administrador",
    "mmanresa@grupobca.com.ar": "Gerente",
    "aescobar@grupobca.com.ar": "Tráfico",
    "monitoreo@grupobca.com.ar": "Monitoreo",
    "taller@grupobca.com.ar": "Taller",
}

ROLES_PERMITIDOS = {
    "Administrador": ["1_programacion", "2_dia_operativo", "2_viajes", "4_eventos"],
    "Gerente": ["1_programacion", "2_dia_operativo", "2_viajes", "4_eventos"],
    "Tráfico": ["1_programacion", "2_dia_operativo", "2_viajes"],
    "Monitoreo": ["2_dia_operativo", "2_viajes"],
    "Taller": ["4_eventos"],
}

# -------------------------------------------------
# LOGIN SIMPLE POR MAIL
# -------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 Acceso al sistema")

    email = st.text_input("Correo corporativo")
    ingresar = st.button("Ingresar")

    if ingresar:
        if email in USERS:
            st.session_state.user = {"email": email, "rol": USERS[email]}
            st.rerun()
        else:
            st.error("Usuario no autorizado")

    st.stop()

user = st.session_state.user
rol = user["rol"]

# -------------------------------------------------
# IMPORTACIÓN DE MAESTROS (EXCEL) - DESPUÉS DE INIT_DB
# (Se ejecuta ya logueado para evitar ruido en cada refresh)
# -------------------------------------------------
from services.maestros.choferes import importar_si_cambio as importar_choferes
from services.maestros.tractores import importar_si_cambio as importar_tractores
from services.maestros.materiales import importar_si_cambio as importar_materiales
from services.maestros.clientes import importar_si_cambio as importar_clientes
from services.maestros.origenes import importar_si_cambio as importar_origenes
from services.maestros.destinos import importar_si_cambio as importar_destinos

# Evita re-importar en cada rerun (muy importante en Streamlit)
if "maestros_importados" not in st.session_state:
    st.session_state.maestros_importados = False

if not st.session_state.maestros_importados:
    importar_choferes(conn, "data/excels/Base_Choferes.xlsx")
    importar_tractores(conn, "data/excels/Base_Tractores.xlsx")
    importar_materiales(conn, "data/excels/Base_Materiales.xlsx")
    importar_clientes(conn, "data/excels/Base_Clientes.xlsx")
    importar_origenes(conn, "data/excels/Base_Origenes.xlsx")
    importar_destinos(conn, "data/excels/Base_Destinos.xlsx")
    st.session_state.maestros_importados = True

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("🚛 BCA")
st.sidebar.write(f"👤 {user['email']}")
st.sidebar.write(f"Rol: **{rol}**")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.user = None
    st.session_state.maestros_importados = False
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📂 Módulos")

permitidos = ROLES_PERMITIDOS.get(rol, [])

# -------------------------------------------------
# MENÚ DE NAVEGACIÓN
# -------------------------------------------------
if "1_programacion" in permitidos:
    st.sidebar.page_link("pages/1_programacion.py", label="📆 Programación Semanal")

if "2_dia_operativo" in permitidos:
    st.sidebar.page_link("pages/2_dia_operativo.py", label="🟨 Día Operativo")

if "2_viajes" in permitidos:
    st.sidebar.page_link("pages/2_viajes.py", label="🟩 Viajes")

if "4_eventos" in permitidos:
    st.sidebar.page_link("pages/4_eventos.py", label="🔧 Eventos")

# -------------------------------------------------
# HOME
# -------------------------------------------------
st.title("🚛 Programación y Monitoreo BCA")

st.markdown(
    """
### Bienvenido al sistema

Este sistema permite:
- 📆 Planificar la semana (proyección)
- 🟨 Ejecutar y monitorear el día operativo
- 🟩 Analizar viajes confirmados
- 🔧 Registrar eventos operativos sobre viajes

👉 Enfocado 100% en **planificación, ejecución y desvíos**.
"""
)

st.success("Sistema inicializado correctamente y listo para operar.")
