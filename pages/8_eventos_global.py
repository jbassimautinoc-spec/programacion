import streamlit as st
import pandas as pd
from datetime import date, datetime

from utils.db import get_connection
from services.eventos_globales import listar_eventos_globales
from services.maestros.choferes import listar_choferes
from services.maestros.tractores import listar_tractores
from io import BytesIO


# =================================================
# Configuración página
# =================================================
st.set_page_config(page_title="Eventos – Vista Global", layout="wide")

st.markdown("""
<style>
section[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión.")
    st.stop()

st.title("📋 Eventos – Vista Global")

conn = get_connection()



# =================================================
# Filtros (con FORM)
# =================================================
st.subheader("🔎 Filtros")

choferes = listar_choferes(conn)
tractores = listar_tractores(conn)

with st.form("filtros_eventos_globales"):

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        desde = st.date_input(
            "Desde",
            value=date.today().replace(day=1)
        )

    with c2:
        hasta = st.date_input(
            "Hasta",
            value=date.today()
        )

    with c3:
        chofer_sel = st.selectbox(
            "Chofer",
            options=[None] + [c["id_chofer"] for c in choferes],
            format_func=lambda x: "Todos" if x is None else next(
                c["nombre"] for c in choferes if c["id_chofer"] == x
            )
        )

    with c4:
        st.selectbox(
        "Tractor",
        options=["Pendiente de asignación en viajes"],
        disabled=True
        )

        

    tipos = st.multiselect(
         "Tipo de evento",
    [
        "Demora carga",
        "Demora descarga",
        "RRHH",
        "Clima / viento",
        "Cliente",
        "Documentación",
        "Cancelación operativa",
        "Falla mecánica en ruta",
        "Demora taller"
    ]
)

    aplicar = st.form_submit_button("Aplicar filtros")

if not aplicar:
    st.stop()


# =================================================
# Cargar eventos
# =================================================
eventos = listar_eventos_globales(
    conn,
    desde=desde,
    hasta=hasta,
    tipo=tipos[0] if tipos else None,
    chofer_id=chofer_sel,
    tractor_id=None
)



if not eventos:
    st.info("No hay eventos con esos filtros.")
    st.stop()


# =================================================
# Preparar DataFrame
# =================================================
rows = []

for e in eventos:
    inicio_dt = datetime.fromisoformat(e["inicio_ts"])
    fin_dt = datetime.fromisoformat(e["fin_ts"]) if e["fin_ts"] else None

    if fin_dt:
        delta = fin_dt - inicio_dt
        horas, rem = divmod(int(delta.total_seconds()), 3600)
        minutos = rem // 60
        duracion = f"{horas:02}:{minutos:02} h"
    else:
        duracion = "En curso"

    rows.append({
        "Inicio": inicio_dt.strftime("%Y-%m-%d %H:%M"),
        "Fin": fin_dt.strftime("%Y-%m-%d %H:%M") if fin_dt else "—",
        "Duración": duracion,
        "Tipo": e["tipo"],
        "Chofer": e.get("chofer_nombre") or e.get("chofer_id") or "—",
        "Tractor": e.get("tractor_id") or "—",
        "Observación": e.get("observacion") or ""
    })

df = pd.DataFrame(rows)

df = pd.DataFrame(rows)

# =================================================
# Exportar (según filtros aplicados)
# =================================================
buffer = BytesIO()
df.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    label="📤 Exportar eventos (según filtros)",
    data=buffer,
    file_name=f"eventos_globales_{desde}_{hasta}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.dataframe(df, use_container_width=True)



# =================================================
# KPI – Horas por tipo de evento
# =================================================
st.subheader("📊 KPI – Horas por tipo de evento")

kpi = {}

for e in eventos:
    if not e["fin_ts"]:
        continue

    inicio = datetime.fromisoformat(e["inicio_ts"])
    fin = datetime.fromisoformat(e["fin_ts"])
    horas = (fin - inicio).total_seconds() / 3600

    kpi[e["tipo"]] = kpi.get(e["tipo"], 0) + horas

if not kpi:
    st.info("No hay eventos cerrados para calcular KPIs.")
else:
    df_kpi = (
        pd.DataFrame([
            {"Tipo de evento": k, "Horas totales": round(v, 2)}
            for k, v in kpi.items()
        ])
        .sort_values("Horas totales", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(df_kpi, use_container_width=True)
