import streamlit as st
from datetime import date, datetime
from services.disponibilidad import pool_disponibilidad_diaria

# -------------------------
# Configuración página
# -------------------------
st.set_page_config(
    page_title="Día Operativo",
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

# -------------------------
# Seguridad
# -------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión para acceder.")
    st.stop()

# -------------------------
# Imports
# -------------------------
from utils.db import get_connection
from modules.dia_operativo import (
    obtener_lineas_del_dia,
    kpis_dia,
    crear_fuera_de_programacion
)
from services.maestros.choferes import listar_choferes
from services.maestros.tractores import listar_tractores
from services.maestros.materiales import listar_materiales

# -------------------------
# Helpers
# -------------------------
def parse_fecha(x):
    if isinstance(x, date):
        return x
    x = str(x).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(x, fmt).date()
        except ValueError:
            pass
    return date.fromisoformat(x)

# -------------------------
# UI
# -------------------------
st.title("🟨 Día Operativo")

conn = get_connection()

# -------------------------
# Fecha
# -------------------------
if "dia_operativo_fecha" not in st.session_state:
    st.session_state.dia_operativo_fecha = date.today()

fecha = st.date_input(
    "Fecha",
    value=st.session_state.dia_operativo_fecha,
    key="dia_operativo_fecha"
)

if hasattr(fecha, "date"):
    fecha = fecha.date()

st.caption(f"Día operativo: **{fecha.strftime('%d/%m/%Y')}**")

# -------------------------
# Pool disponibilidad
# -------------------------
pool = pool_disponibilidad_diaria(conn, fecha)

st.subheader("🚦 Disponibilidad flota")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🚛 Tractores", pool["tractores_total"])
c2.metric("🛠️ En mantenimiento", pool["tractores_mantenimiento"])
c3.metric("👨‍✈️ Choferes disponibles", pool["choferes_disponibles"])
c4.metric("✅ Pool disponible", pool["pool_disponible"])

# -------------------------
# KPIs día
# -------------------------
stats = kpis_dia(conn, fecha)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total viajes", stats["total"])
c2.metric("Confirmados", stats["confirmados"])
c3.metric("Cancelados", stats["cancelados"])
c4.metric("Fuera de plan", stats["fuera_plan"])

# -------------------------
# Líneas del día
# -------------------------
st.subheader("📋 Viajes del día")

# mapa chofer id -> nombre
choferes = listar_choferes(conn)
map_chofer = {c["id_chofer"]: c["nombre"] for c in choferes}

lineas_raw = obtener_lineas_del_dia(conn, fecha)

if not lineas_raw:
    st.info("No hay viajes para este día.")
else:
    lineas = []
    for l in lineas_raw:
        lf = parse_fecha(l["fecha"])
        l["_fecha"] = lf

        # resolver nombre de chofer si viene id
        ch = l.get("chofer")
        if ch in map_chofer:
            l["chofer"] = map_chofer[ch]

        lineas.append(l)

    lineas.sort(key=lambda x: (x["_fecha"], x.get("chofer", "")))

    for l in lineas:
        titulo = (
            f"{l.get('chofer', 'SIN CHOFER')} | "
            f"{l.get('tractor', 'SIN TRACTOR')} | "
            f"{l.get('origen_linea', '—')} | "
            f"{l.get('estado', '—')}"
        )

        with st.expander(titulo):
            st.write(f"**Fecha:** {l['_fecha'].strftime('%d/%m/%Y')}")
            st.write(f"**Chofer:** {l.get('chofer', '—')}")
            st.write(f"**Tractor:** {l.get('tractor', '—')}")
            st.write(f"**Estado:** {l.get('estado', '—')}")
            st.write(f"**Origen:** {l.get('origen_linea', '—')}")

# -------------------------
# Fuera de programación
# -------------------------
st.subheader("➕ Viaje fuera de programación")

tractores = listar_tractores(conn)
materiales = listar_materiales(conn)

if not choferes or not tractores or not materiales:
    st.warning("Faltan maestros cargados")
else:
    with st.form("fuera_plan"):
        chofer_id = st.selectbox(
            "Chofer",
            [c["id_chofer"] for c in choferes],
            format_func=lambda cid: map_chofer.get(cid, cid)
        )

        tractor_id = st.selectbox(
            "Tractor",
            [t["id_tractor"] for t in tractores],
            format_func=lambda tid: next(
                x["patente"] for x in tractores if x["id_tractor"] == tid
            )
        )

        material_id = st.selectbox(
            "Material",
            [m["id_material"] for m in materiales],
            format_func=lambda mid: next(
                x["material"] for x in materiales if x["id_material"] == mid
            )
        )

        if st.form_submit_button("Agregar"):
            crear_fuera_de_programacion(
                conn,
                fecha,
                chofer_id,
                tractor_id,
                material_id,
                "ui"
            )
            st.success("Viaje agregado")
            st.rerun()
