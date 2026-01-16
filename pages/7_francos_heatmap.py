import streamlit as st
import pandas as pd
from datetime import date, timedelta
from calendar import monthrange

st.set_page_config(page_title="Francos – Vista Mensual", layout="wide")

st.markdown(
    """
    <style>
        section[data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión para acceder.")
    st.stop()

from utils.db import get_connection
from services.maestros.choferes import listar_choferes
from services.eventos_recursos import listar_francos_mes

st.title("🗓️ Francos – Vista Mensual (Flota Propia)")

conn = get_connection()
hoy = date.today()

c1, c2 = st.columns(2)
with c1:
    year = st.selectbox("Año", options=list(range(hoy.year - 2, hoy.year + 2)), index=2)
with c2:
    month = st.selectbox("Mes", options=list(range(1, 13)), index=hoy.month - 1)

choferes = listar_choferes(conn)
francos = listar_francos_mes(conn, year, month) or []

dias_mes = monthrange(year, month)[1]
dias = list(range(1, dias_mes + 1))

# =========================
# Heatmap
# =========================
data = []
for ch in choferes:
    fila = {"Chofer": ch["nombre"]}
    for d in dias:
        fecha_dia = date(year, month, d)
        en_franco = any(
            f.get("recurso_id") == ch["id_chofer"]
            and date.fromisoformat(f["fecha_inicio"]) <= fecha_dia <= date.fromisoformat(f["fecha_fin"])
            for f in francos
        )
        fila[d] = "🟥" if en_franco else ""
    data.append(fila)

df = pd.DataFrame(data)
st.caption("🟥 Franco | vacío = disponible")
st.dataframe(df, use_container_width=True, height=600)

# =========================
# KPI
# =========================
st.subheader("📊 Días de franco por chofer (mes)")
solo_con_franco = st.checkbox("Mostrar solo choferes con franco (>0)", value=True)

dias_por_chofer = {ch["id_chofer"]: set() for ch in choferes}
inicio_mes = date(year, month, 1)
fin_mes = date(year, month, monthrange(year, month)[1])

for f in francos:
    cid = f.get("recurso_id")
    if cid not in dias_por_chofer:
        continue

    fi = date.fromisoformat(f["fecha_inicio"])
    ff = date.fromisoformat(f["fecha_fin"])

    if ff < inicio_mes or fi > fin_mes:
        continue

    fi = max(fi, inicio_mes)
    ff = min(ff, fin_mes)

    d = fi
    while d <= ff:
        dias_por_chofer[cid].add(d)
        d += timedelta(days=1)

data_kpi = []
for ch in choferes:
    cid = ch["id_chofer"]
    dias_franco = len(dias_por_chofer.get(cid, set()))
    if solo_con_franco and dias_franco == 0:
        continue
    data_kpi.append({"Chofer": ch["nombre"], "Días de franco": dias_franco})

# 👇 CLAVE: siempre crear columnas aunque esté vacío
df_kpi = pd.DataFrame(data_kpi, columns=["Chofer", "Días de franco"])

if df_kpi.empty:
    st.info("No hay francos cargados en este mes.")
else:
    df_kpi = df_kpi.sort_values("Días de franco", ascending=False).reset_index(drop=True)
    st.dataframe(df_kpi, use_container_width=True)
