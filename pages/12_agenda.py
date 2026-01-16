import streamlit as st
from datetime import date, timedelta, datetime

from utils.db import get_connection
from services.agenda import listar_viajes_agenda
from services.maestros.choferes import listar_choferes

# =================================================
# Configuración página
# =================================================
st.set_page_config(page_title="Agenda Operativa", layout="wide")
st.title("📅 Agenda Operativa")

# =================================================
# Seguridad
# =================================================
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión.")
    st.stop()

# =================================================
# Helpers fechas
# =================================================
def lunes_de_semana(d: date) -> date:
    return d - timedelta(days=d.weekday())

def domingo_de_semana(d: date) -> date:
    return lunes_de_semana(d) + timedelta(days=6)

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

# =================================================
# Inicialización estado
# =================================================
if "agenda_fecha_base" not in st.session_state:
    st.session_state.agenda_fecha_base = lunes_de_semana(date.today())

if st.button("🧹 Reset Agenda", key="reset_agenda"):
    st.session_state.agenda_fecha_base = lunes_de_semana(date.today())
    st.rerun()

# =================================================
# Selector semana
# =================================================
c1, c2, c3 = st.columns([1, 4, 1])

with c1:
    if st.button("◀", key="semana_atras"):
        st.session_state.agenda_fecha_base -= timedelta(days=7)
        st.rerun()

with c3:
    if st.button("▶", key="semana_adelante"):
        st.session_state.agenda_fecha_base += timedelta(days=7)
        st.rerun()

fecha_base = st.session_state.agenda_fecha_base
lunes = fecha_base
domingo = fecha_base + timedelta(days=6)

with c2:
    st.markdown(
        f"<div style='display:none'>Semana del {lunes:%d/%m} al {domingo:%d/%m}</div>",
        unsafe_allow_html=True
    )

# =================================================
# Filtro fechas
# =================================================
with st.expander("🗓️ Filtro de fechas", expanded=False):
    usar_filtro_fechas = st.checkbox("Usar rango de fechas personalizado", value=False)

    if usar_filtro_fechas:
        f1, f2 = st.columns(2)
        with f1:
            fecha_desde = st.date_input("Desde", value=lunes, key="agenda_desde")
        with f2:
            fecha_hasta = st.date_input("Hasta", value=domingo, key="agenda_hasta")
    else:
        fecha_desde = lunes
        fecha_hasta = domingo

# =================================================
# DB y maestros
# =================================================
conn = get_connection()

choferes = listar_choferes(conn)
MAP_CHOFER = {c["id_chofer"]: c["nombre"] for c in choferes}

# =================================================
# Helpers dominio
# =================================================
MAP_MATERIAL = {"M_01": "Arena", "M_02": "Piedra"}

def material_nombre(v):
    if not v:
        return "-"
    v = str(v).strip().lower()
    if v == "arena":
        return "Arena"
    if v == "piedra":
        return "Piedra"
    return MAP_MATERIAL.get(v.upper(), "-")

def es_viaje_valido(v):
    return v["tipo"] == "VIAJE" and material_nombre(v["material"]) in ("Arena", "Piedra")

# =================================================
# Datos
# =================================================
items_raw = listar_viajes_agenda(conn, fecha_desde, fecha_hasta)

items = []
for v in items_raw:
    f = parse_fecha(v.get("fecha"))
    v["_fecha"] = f

    ch = v.get("chofer")
    if ch in MAP_CHOFER:
        v["chofer"] = MAP_CHOFER[ch]

    items.append(v)

# =================================================
# Filtros tipo
# =================================================
with st.expander("🔎 Filtros", expanded=True):
    f1, f2 = st.columns(2)
    ver_lineas = f1.checkbox("Programados (líneas)", True)
    ver_viajes = f2.checkbox("Viajes generados", True)

items = [
    v for v in items
    if (v["tipo"] == "LINEA" and ver_lineas)
    or (v["tipo"] == "VIAJE" and ver_viajes)
]

# =================================================
# KPIs
# =================================================
arena = sum(
    1 for v in items
    if es_viaje_valido(v) and material_nombre(v["material"]) == "Arena"
)
piedra = sum(
    1 for v in items
    if es_viaje_valido(v) and material_nombre(v["material"]) == "Piedra"
)

st.markdown(
    f"""
    <div style="display:flex; gap:12px; margin:10px 0 14px 0;">
        <span style="background:#FFF4CC; padding:6px 12px; border-radius:10px;">
            🟡 Arena: <b>{arena}</b>
        </span>
        <span style="background:#F0F0F0; padding:6px 12px; border-radius:10px;">
            ⚪ Piedra: <b>{piedra}</b>
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

# =================================================
# Agrupar por día (fecha real)
# =================================================
items_por_dia = {}
for v in items:
    items_por_dia.setdefault(v["_fecha"], []).append(v)

dias_operativos = sorted(items_por_dia.keys())

# =================================================
# Render Agenda
# =================================================
st.divider()
st.subheader("🟢 Agenda por Día Operativo")

if not dias_operativos:
    st.info("No hay actividad en el período seleccionado.")
else:
    cols = st.columns(len(dias_operativos))

    for idx, dia in enumerate(dias_operativos):
        with cols[idx]:
            st.markdown(f"### 📅 {dia.strftime('%d/%m/%Y')}")

            items_dia = items_por_dia.get(dia, [])
            if not items_dia:
                st.caption("Sin registros")
                continue

            choferes_con_viaje = {
                v.get("chofer")
                for v in items_dia
                if v.get("tipo") == "VIAJE" and v.get("chofer")
            }

            items_visibles = [
                v for v in items_dia
                if not (
                    v.get("tipo") == "LINEA"
                    and v.get("chofer") in choferes_con_viaje
                )
            ]

            for v in items_visibles:
                icono = "🟢" if v.get("tipo") == "VIAJE" else "🟡"
                st.write(
                    f"{icono} {v.get('tipo')} | "
                    f"{v.get('chofer','-')} | "
                    f"{material_nombre(v.get('material'))} | "
                    f"{v.get('estado','-')}"
                )
