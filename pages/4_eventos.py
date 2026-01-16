import streamlit as st
from datetime import date, time, datetime

# =================================================
# Configuración página
# =================================================
st.set_page_config(
    page_title="Eventos de Viaje",
    layout="wide"
)

st.markdown(
    """
    <style>
        section[data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =================================================
# Seguridad
# =================================================
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión para acceder.")
    st.stop()

# =================================================
# Path fix
# =================================================
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =================================================
# Imports backend
# =================================================
from utils.db import get_connection
from services.viajes import listar_viajes_activos
from services.eventos_viaje import (
    crear_evento_viaje,
    listar_eventos_viaje
)

# =================================================
# UI
# =================================================
st.title("🔧 Eventos de Viaje")

conn = get_connection()

# =================================================
# Selector de viaje
# =================================================
viajes = listar_viajes_activos(conn)

if not viajes:
    st.info("No hay viajes activos.")
    st.stop()

viaje_id = st.selectbox(
    "Viaje",
    [v["id"] for v in viajes],   # 🔴 CORREGIDO
    format_func=lambda vid: next(
        f"{x['fecha']} | {x['chofer']} | {x['material']}"
        for x in viajes
        if x["id"] == vid         # 🔴 CORREGIDO
    )
)

# =================================================
# Eventos del viaje
# =================================================
st.subheader("📋 Eventos del viaje")

eventos = listar_eventos_viaje(conn, viaje_id)

if eventos:
    st.dataframe(eventos, use_container_width=True)
else:
    st.info("Sin eventos cargados.")

# =================================================
# Nuevo evento
# =================================================
st.subheader("➕ Nuevo evento")

with st.form("nuevo_evento"):
    tipo = st.selectbox(
        "Tipo de evento",
        [
            "DEMORA_CARGA",
            "DEMORA_DESCARGA",
            "DEMORA_CHOFER",
            "RRHH",
            "CLIMA_VIENTO",
            "CLIENTE",
            "DOCUMENTACION",
            "CANCELACION_OPERATIVA",
            "FALLA_MECANICA_RUTA",
            "DEMORA_TALLER",
        ]
    )

    observacion = st.text_area("Observación")

    st.markdown("### ⏱️ Tiempo del evento")

    c1, c2 = st.columns(2)
    with c1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today())
        hora_inicio = st.time_input("Hora inicio", value=time(8, 0))
    with c2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())
        hora_fin = st.time_input("Hora fin", value=time(9, 0))

    submit = st.form_submit_button("Guardar evento")

    if submit:
        inicio_dt = datetime.combine(fecha_inicio, hora_inicio)
        fin_dt = datetime.combine(fecha_fin, hora_fin)

        if fin_dt <= inicio_dt:
            st.error("La fecha/hora de fin debe ser posterior al inicio.")
            st.stop()

        try:
            crear_evento_viaje(
                conn,
                viaje_id,
                tipo,
                inicio_dt,
                fin_dt,
                observacion,
                st.session_state.user["email"]
            )

            st.success("Evento registrado correctamente.")
            st.rerun()

        except Exception as e:
            st.error(str(e))
