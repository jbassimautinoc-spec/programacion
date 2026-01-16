import sys
from pathlib import Path
from datetime import date, timedelta
import streamlit as st
import pandas as pd
from io import BytesIO

# -------------------------
# Configuración página
# -------------------------
st.set_page_config(page_title="Programación Semanal", layout="wide")

st.markdown(
    """
    <style>
        section[data-testid="stSidebarNav"] { display: none; }
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
# Path raíz
# -------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -------------------------
# Imports
# -------------------------
from utils.db import get_connection
from services.programacion.semanal import (
    generar_programacion_semanal,
    contadores_semana,
    listar_programacion_semana,
    eliminar_linea_programacion,
)
from services.programacion.disponibilidad import (
    contadores_choferes,
    contadores_tractores,
    listar_tractores_sueltos,
)
from services.maestros.choferes import listar_choferes
from services.maestros.materiales import listar_materiales

# -------------------------
# UI
# -------------------------
st.title("📆 Programación Semanal")
conn = get_connection()

# =================================================
# Semana
# =================================================
if "lunes_semana" not in st.session_state:
    hoy = date.today()
    st.session_state.lunes_semana = hoy - timedelta(days=hoy.weekday())

fecha_input = st.date_input(
    "Semana (seleccionar un día)",
    value=st.session_state.lunes_semana,
)

lunes_semana = fecha_input - timedelta(days=fecha_input.weekday())
st.session_state.lunes_semana = lunes_semana
domingo_semana = lunes_semana + timedelta(days=6)

st.caption(
    f"Semana del **{lunes_semana.strftime('%d/%m/%Y')}** "
    f"al **{domingo_semana.strftime('%d/%m/%Y')}**"
)

# =================================================
# Estado semana
# =================================================
cur = conn.cursor()
cur.execute(
    """
    SELECT COUNT(*) 
    FROM lineas_dia 
    WHERE fecha BETWEEN ? AND ?
      AND origen_linea = 'PROGRAMACION'
      AND estado = 'CONFIRMADO'
    """,
    (lunes_semana.isoformat(), domingo_semana.isoformat())
)
semana_confirmada = cur.fetchone()[0] > 0

# =================================================
# KPIs
# =================================================
stats = contadores_semana(conn, lunes_semana)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Líneas programadas", stats["total"])
c2.metric("Arena", stats["arena"])
c3.metric("Piedra", stats["piedra"])
c4.metric("Choferes programados", stats["choferes_programados"])

# =================================================
# Disponibilidad
# =================================================
with st.expander("ℹ️ Disponibilidad de recursos"):
    stats_ch = contadores_choferes(conn, lunes_semana)
    stats_tr = contadores_tractores(conn, lunes_semana)
    tractores_sueltos = listar_tractores_sueltos(conn)

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Choferes disponibles", stats_ch["disponibles"])
    d2.metric("Choferes no disponibles", stats_ch["no_disponibles"])
    d3.metric("🟡 Pendientes de programar", stats_ch["pendientes_programar"])
    d4.metric("Tractores disponibles", stats_tr["disponibles"])
    d5.metric("Tractores no disponibles", stats_tr["no_disponibles"])
    d6.metric("🚛 Operativos sin chofer", len(tractores_sueltos))

# =================================================
# Generar programación
# =================================================
st.subheader("🧩 Generar Programación")

choferes = listar_choferes(conn)
materiales = listar_materiales(conn)

DIAS_SEMANA = [
    "Lunes", "Martes", "Miércoles",
    "Jueves", "Viernes", "Sábado", "Domingo"
]

if not semana_confirmada:
    with st.form("generar_semana"):
        choferes_sel = st.multiselect(
            "Choferes",
            options=[c["id_chofer"] for c in choferes],
            format_func=lambda cid: next(
                x["nombre"] for x in choferes if x["id_chofer"] == cid
            )
        )

        dias_sel = st.multiselect("Días", options=DIAS_SEMANA)

        material_id = st.selectbox(
            "Material",
            options=[m["id_material"] for m in materiales],
            format_func=lambda mid: next(
                x["material"] for x in materiales if x["id_material"] == mid
            )
        )

        submit = st.form_submit_button("Generar programación")

        if submit:
            if not choferes_sel or not dias_sel:
                st.warning("Seleccioná al menos un chofer y un día")
            else:
                res = generar_programacion_semanal(
                    conn=conn,
                    fecha_desde=lunes_semana,
                    choferes_ids=choferes_sel,
                    dias=dias_sel,
                    material_id=material_id,
                    usuario=st.session_state.user["email"]
                )
                st.success(
                    f"Programación creada: {res['creadas']} "
                    f"(omitidas: {res['omitidas']})"
                )
                st.rerun()

# =================================================
# Líneas Programadas
# =================================================
st.subheader("📋 Líneas Programadas")

rows = listar_programacion_semana(conn, lunes_semana)

if not rows:
    st.info("No hay programación para esta semana")
    st.stop()

df = pd.DataFrame(rows)

vista = st.radio(
    "Vista",
    ["📋 Tabla", "🗓️ Agenda por día"],
    horizontal=True
)

# =================================================
# EXPORTAR
# =================================================
buffer = BytesIO()
df.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    "📤 Exportar líneas a Excel",
    data=buffer,
    file_name=f"lineas_programadas_{lunes_semana}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =================================================
# VISTA TABLA
# =================================================
if vista.startswith("📋"):
    modo_edicion = st.toggle("✏️ Editar programación", disabled=semana_confirmada)

    for r in rows:
        c1, c2, c3, c4, c5 = st.columns([2, 4, 3, 2, 1])
        c1.write(r["fecha"])
        c2.write(r["chofer"])
        c3.write(r["material"])
        c4.write(r["estado"])

        if modo_edicion and not semana_confirmada:
            if c5.button("🗑️", key=f"del_{r['id']}"):
                eliminar_linea_programacion(conn, r["id"])
                st.rerun()

# =================================================
# VISTA AGENDA
# =================================================
else:
    items_por_dia = {}
    for r in rows:
        items_por_dia.setdefault(r["fecha"], []).append(r)

    dias = sorted(items_por_dia.keys())
    cols = st.columns(len(dias))

    for idx, dia in enumerate(dias):
        with cols[idx]:
            st.markdown(f"### 📅 {dia}")
            for r in items_por_dia[dia]:
                st.write(
                    f"🟡 {r['chofer']} | {r['material']} | {r['estado']}"
                )

# =================================================
# Confirmar programación
# =================================================
st.divider()

if semana_confirmada:
    st.success("📸 Programación semanal CONFIRMADA")
    st.stop()

st.warning("⚠️ Programación en BORRADOR")

if st.button("📸 Confirmar programación semanal"):
    cur = conn.cursor()
    cur.execute("""
        UPDATE lineas_dia
        SET estado = 'CONFIRMADO'
        WHERE fecha BETWEEN ? AND ?
          AND origen_linea = 'PROGRAMACION'
    """, (lunes_semana.isoformat(), domingo_semana.isoformat()))
    conn.commit()
    st.rerun()
