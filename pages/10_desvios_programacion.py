import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils.db import get_connection
from services.desvios import (
    calcular_desvios_dia,
    calcular_resumen_semana
)

# =================================================
# Configuración página
# =================================================
st.set_page_config(
    page_title="Desvíos vs Programación",
    layout="wide"
)

st.markdown("""
<style>
section[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# =================================================
# Seguridad
# =================================================
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión.")
    st.stop()

# =================================================
# Conexión
# =================================================
conn = get_connection()




st.title("📊 Desvíos vs Programación")

# =================================================
# Selector de fecha
# =================================================
st.subheader("📅 Seleccionar día operativo")

with st.form("selector_fecha_desvios"):
    fecha_sel = st.date_input(
        "Día a analizar",
        value=date.today()
    )
    aplicar = st.form_submit_button("Aplicar")

if not aplicar:
    st.stop()


# Calcular semana
lunes = fecha_sel - timedelta(days=fecha_sel.weekday())
domingo = lunes + timedelta(days=6)

st.caption(
    f"Semana analizada: **{lunes.strftime('%d/%m/%Y')}** "
    f"al **{domingo.strftime('%d/%m/%Y')}**"
)

# =================================================
# KPIs SEMANALES
# =================================================
st.subheader("📈 Resumen semanal")

resumen_dias = calcular_resumen_semana(conn, fecha_sel)

total_programado = sum(r["programadas"] for r in resumen_dias) if resumen_dias else 0
total_ejecutado  = sum(r["ejecutadas"] for r in resumen_dias) if resumen_dias else 0
total_desviado   = sum(r["desviadas"] for r in resumen_dias) if resumen_dias else 0

cumplimiento = round(
    (total_ejecutado / total_programado) * 100, 1
) if total_programado else 0

# 👉 contenedor para evitar “valores enganchados”
with st.container():
    
    kpi_placeholder = st.empty()

with kpi_placeholder.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total programado", total_programado)
    c2.metric("Ejecutadas", total_ejecutado)
    c3.metric("Desvíos", total_desviado)
    c4.metric("Cumplimiento %", f"{cumplimiento} %")


# Resumen por día
if resumen_dias:
    st.dataframe(
        pd.DataFrame(resumen_dias),
        use_container_width=True
    )
else:
    st.info("No hay programación confirmada para esa semana.")

# =================================================
# DETALLE DIARIO
# =================================================
st.subheader("📋 Detalle del día")

detalles = calcular_desvios_dia(conn, fecha_sel)

if not detalles:
    st.info("No hay programación confirmada para ese día.")
    st.stop()

df = pd.DataFrame(detalles)

df["resultado"] = pd.Categorical(
    df["resultado"],
    categories=["OK", "CAMBIO_MATERIAL", "NO_EJECUTADO"],
    ordered=True
)

df = df.sort_values(["resultado", "chofer_nombre"])

st.dataframe(
    df[
        [
            "chofer_nombre",
            "material_programado",
            "material_ejecutado",
            "resultado"
        ]
    ],
    use_container_width=True
)

# =================================================
# EXPORTAR
# =================================================
st.divider()
st.subheader("⬇️ Exportar desvíos")

df_resumen = pd.DataFrame(resumen_dias)
df_detalle = pd.DataFrame(detalles)

file_name = f"desvios_programacion_{lunes}_{domingo}.xlsx"

with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
    df_resumen.to_excel(writer, sheet_name="Resumen semanal", index=False)
    df_detalle.to_excel(writer, sheet_name="Detalle diario", index=False)

with open(file_name, "rb") as f:
    st.download_button(
        label="📥 Descargar Excel de desvíos",
        data=f,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =================================================
# LEYENDA
# =================================================
with st.expander("ℹ️ Cómo se interpreta"):
    st.markdown("""
- **OK**: se ejecutó el viaje con el material programado  
- **NO_EJECUTADO**: la línea quedó programada pero no se ejecutó  
- **CAMBIO_MATERIAL**: se ejecutó, pero con otro material  

Criterios:
- Programación **CONFIRMADA**
- Asociación por **fecha + chofer**
""")
