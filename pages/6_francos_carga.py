import streamlit as st
import sqlite3
from datetime import date

# =================================================
# Configuración página
# =================================================
st.set_page_config(
    page_title="Francos – Flota Propia",
    layout="wide"
)

st.markdown(
    """
    <style>
        section[data-testid="stSidebarNav"] { display: none; }
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
# Imports
# =================================================
from utils.db import get_connection
from services.maestros.choferes import listar_choferes
from services.eventos_recursos import iniciar_franco, finalizar_franco

# =================================================
# UI
# =================================================
st.title("🟦 Francos – Flota Propia")

conn = get_connection()
conn.row_factory = sqlite3.Row

# =================================================
# Choferes
# =================================================
choferes = listar_choferes(conn)

if not choferes:
    st.info("No hay choferes activos cargados.")
    st.stop()

chofer_map = {c["id_chofer"]: c["nombre"] for c in choferes}

chofer_id = st.selectbox(
    "Chofer",
    options=list(chofer_map.keys()),
    format_func=lambda cid: chofer_map.get(cid, cid)
)

# =================================================
# Cargar franco
# =================================================
st.subheader("➕ Cargar franco")

c1, c2 = st.columns(2)
with c1:
    fecha_inicio = st.date_input("Fecha inicio", value=date.today())

with c2:
    fecha_fin = st.date_input("Fecha fin", value=date.today())

if fecha_fin < fecha_inicio:
    st.error("La fecha fin no puede ser anterior a la fecha inicio.")
else:
    if st.button("Registrar franco"):
        iniciar_franco(
            conn=conn,
            chofer_id=chofer_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            usuario=st.session_state.user.get("email", "ui")
        )
        st.success("Franco registrado.")
        st.rerun()

# =================================================
# Francos del chofer (LISTADO REAL)
# =================================================
st.subheader("📋 Francos del chofer")

cur = conn.cursor()
cur.execute(
    """
    SELECT
        id,
        fecha_inicio,
        fecha_fin
    FROM eventos
    WHERE tipo = 'FRANCO'
      AND recurso_tipo = 'CHOFER'
      AND recurso_id = ?
    ORDER BY fecha_inicio DESC
    """,
    (chofer_id,),
)

francos = cur.fetchall()

if not francos:
    st.info("El chofer no tiene francos cargados.")
else:
    total_dias = 0

    for f in francos:
        fi = date.fromisoformat(f["fecha_inicio"])
        ff = date.fromisoformat(f["fecha_fin"])
        dias = (ff - fi).days + 1
        total_dias += dias

        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"📅 {f['fecha_inicio']} → {f['fecha_fin']}  |  **{dias} días**")

        with col2:
            if st.button("Finalizar", key=f"fin_{f['id']}"):
                finalizar_franco(
                    conn=conn,
                    evento_id=f["id"],
                    fecha_fin=date.today()
                )
                st.rerun()

    st.markdown(f"### 🧮 Total días de franco: **{total_dias}**")
