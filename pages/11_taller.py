import streamlit as st
from datetime import date
import pandas as pd

from utils.db import get_connection
from services.taller import (
    iniciar_mantenimiento_correctivo,
    listar_tractores_en_mantenimiento
)
from services.maestros.tractores import listar_tractores

# =================================================
# Configuración
# =================================================
st.set_page_config(
    page_title="Taller – Mantenimiento",
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

st.title("🔧 Taller – Gestión de Mantenimiento")

# =================================================
# Funciones de estado
# =================================================
def pasar_a_mantenimiento_manual(conn, tractor_id: str):
    cur = conn.cursor()
    cur.execute("""
        UPDATE tractores
        SET estado = 'MANTENIMIENTO'
        WHERE id_tractor = ?
    """, (tractor_id,))
    conn.commit()

def volver_a_operativo(conn, tractor_id: str):
    cur = conn.cursor()
    cur.execute("""
        UPDATE tractores
        SET estado = 'OPERATIVO'
        WHERE id_tractor = ?
    """, (tractor_id,))
    conn.commit()

# =================================================
# TRACTORES – VISIBILIDAD POR ESTADO
# =================================================
st.subheader("🧰 Tractores – Estado general")

tractores_base = [
    dict(t) for t in listar_tractores(conn)
    if dict(t).get("tipo_flota") == "PROPIA"
]

if not tractores_base:
    st.info("No hay tractores cargados.")
else:
    df = pd.DataFrame(tractores_base)

    # Normalizar columna estado
    if "estado" not in df.columns:
        for posible in ("estado_tractor", "estado_actual"):
            if posible in df.columns:
                df["estado"] = df[posible]
                break

    if "estado" not in df.columns:
        st.error("Los tractores no tienen estado definido.")
    else:
        # -----------------------------
        # Conjuntos
        # -----------------------------
        if "id_chofer" in df.columns:
            df_operativos = df[
                (df["estado"] == "OPERATIVO") &
                (df["id_chofer"].notna())
            ]
            df_base_campana = df[
                (df["estado"] == "OPERATIVO") &
                (df["id_chofer"].isna())
            ]
        else:
            df_operativos = df[df["estado"] == "OPERATIVO"]
            df_base_campana = df.iloc[0:0]

        df_mantenimiento = df[df["estado"] == "MANTENIMIENTO"]

        # -----------------------------
        # Contadores
        # -----------------------------
        total = len(df)
        operativos = len(df_operativos)
        mantenimiento = len(df_mantenimiento)
        base_campana = len(df_base_campana)

        # -----------------------------
        # Selector
        # -----------------------------
        opcion = st.selectbox(
            "Ver tractores",
            [
                f"Base Campana ({base_campana})",
                f"Operativos ({operativos})",
                f"En mantenimiento ({mantenimiento})",
                f"Todos ({total})"
            ]
        )

        # -----------------------------
        # Filtro
        # -----------------------------
        if opcion.startswith("Base Campana"):
            df_filtrado = df_base_campana
            mostrar_boton_mant = True
        elif opcion.startswith("Operativos"):
            df_filtrado = df_operativos
            mostrar_boton_mant = False
        elif opcion.startswith("En mantenimiento"):
            df_filtrado = df_mantenimiento
            mostrar_boton_mant = False
        else:
            df_filtrado = df
            mostrar_boton_mant = False

        for _, row in df_filtrado.sort_values(by="patente").iterrows():
            c1, c2, c3 = st.columns([3, 2, 2])

            with c1:
                st.write(f"🚛 {row['patente']}")
            with c2:
                st.write(row["estado"])
            with c3:
                if mostrar_boton_mant:
                    if st.button(
                        "🛑 Pasar a mantenimiento",
                        key=f"mant_{row['id_tractor']}"
                    ):
                        pasar_a_mantenimiento_manual(conn, row["id_tractor"])
                        st.success(f"{row['patente']} enviado a mantenimiento.")
                        st.rerun()

# =================================================
# INICIAR MANTENIMIENTO CORRECTIVO
# =================================================
st.subheader("🚛 Iniciar mantenimiento correctivo (rotura)")

tractores = listar_tractores(conn)
tractores_correctivo = [t for t in tractores if t["estado"] == "OPERATIVO"]

if not tractores_correctivo:
    st.info("No hay tractores OPERATIVOS disponibles para correctivo.")
else:
    with st.form("form_mantenimiento_correctivo"):
        c1, c2, c3 = st.columns(3)

        with c1:
            tractor_id = st.selectbox(
                "Tractor (en rotura)",
                options=[t["id_tractor"] for t in tractores_correctivo],
                format_func=lambda x: next(
                    t["patente"]
                    for t in tractores_correctivo
                    if t["id_tractor"] == x
                )
            )

        with c2:
            fecha_inicio = st.date_input("Inicio mantenimiento", value=date.today())
        with c3:
            fecha_fin = st.date_input("Fin estimado", value=date.today())

        observacion = st.text_area(
            "Observación (opcional)",
            placeholder="Ej: Rotura en ruta – caja de cambios"
        )

        confirmar = st.form_submit_button("🛑 Enviar a mantenimiento")

    if confirmar:
        iniciar_mantenimiento_correctivo(
            conn=conn,
            tractor_id=tractor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            usuario=st.session_state.user["email"],
            observacion=observacion
        )
        st.success("Tractor enviado a mantenimiento correctivo.")
        st.rerun()

# =================================================
# TRACTORES EN MANTENIMIENTO → VOLVER A OPERATIVO
# =================================================
st.divider()
st.subheader("🧾 Tractores en mantenimiento")

rows = listar_tractores_en_mantenimiento(conn)

if not rows:
    st.info("No hay tractores en mantenimiento.")
else:
    df_mant = pd.DataFrame([dict(r) for r in rows]).sort_values(by="patente")

    for _, row in df_mant.iterrows():
        c1, c2, c3 = st.columns([3, 2, 2])

        with c1:
            st.write(f"🚛 {row['patente']}")
        with c2:
            st.write("MANTENIMIENTO")
        with c3:
            if st.button("✅ Volver a operativo", key=f"op_{row['id_tractor']}"):
                volver_a_operativo(conn, row["id_tractor"])
                st.success(f"{row['patente']} volvió a OPERATIVO.")
                st.rerun()
