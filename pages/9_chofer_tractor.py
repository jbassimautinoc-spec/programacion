# pages/9_chofer_tractor.py
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from io import BytesIO


# -------------------------
# Configuración página
# -------------------------
st.set_page_config(
    page_title="Chofer ⇄ Tractor",
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

conn = get_connection()
cur = conn.cursor()

st.title("👤🚛 Chofer – Tractor")
st.caption("Buscar un chofer y asignar / modificar su tractor.")

# -------------------------
# Cargar choferes
# -------------------------
cur.execute("""
    SELECT
        ch.id_chofer,
        ch.nombre AS chofer,
        ch.id_tractor,
        t.patente,
        t.estado AS estado_tractor
    FROM choferes ch
    LEFT JOIN tractores t ON t.id_tractor = ch.id_tractor
    WHERE ch.activo = 1
    ORDER BY ch.nombre
""")
choferes = [dict(r) for r in cur.fetchall()]

# -------------------------
# Cargar tractores
# -------------------------
cur.execute("""
    SELECT
        id_tractor,
        patente,
        estado
    FROM tractores
    WHERE activo = 1
    ORDER BY patente
""")
tractores = [dict(r) for r in cur.fetchall()]

if not choferes:
    st.info("No hay choferes activos.")
    st.stop()

# -------------------------
# Buscador
# -------------------------
chofer_sel = st.selectbox(
    "🔍 Buscar chofer",
    options=choferes,
    format_func=lambda x: x["chofer"]
)

st.divider()

# -------------------------
# Vista actual
# -------------------------
st.subheader(f"Chofer: {chofer_sel['chofer']}")

if chofer_sel["id_tractor"]:
    st.success(
        f"🚛 Tractor asignado: {chofer_sel['patente']} "
        f"({chofer_sel.get('estado_tractor', '—')})"
    )
else:
    st.warning("🚫 Sin tractor asignado")

# -------------------------
# Estado edición
# -------------------------
edit_key = f"edit_{chofer_sel['id_chofer']}"
if edit_key not in st.session_state:
    st.session_state[edit_key] = False

# -------------------------
# Botón editar
# -------------------------
if not st.session_state[edit_key]:
    if st.button("✏️ Asignar / Modificar tractor"):
        st.session_state[edit_key] = True
        st.rerun()

# -------------------------
# Modo edición
# -------------------------
if st.session_state[edit_key]:

    st.markdown("### 🔧 Editar asignación")

    opciones = [{"id_tractor": None, "patente": "— SIN TRACTOR —"}] + tractores

    tractor_sel = st.selectbox(
        "Tractor",
        options=opciones,
        index=next(
            (
                i for i, t in enumerate(opciones)
                if t["id_tractor"] == chofer_sel["id_tractor"]
            ),
            0
        ),
        format_func=lambda x: x["patente"]
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("💾 Guardar"):
            cur.execute("""
                UPDATE choferes
                SET id_tractor = ?
                WHERE id_chofer = ?
            """, (
                tractor_sel["id_tractor"],
                chofer_sel["id_chofer"]
            ))
            conn.commit()

            st.session_state[edit_key] = False
            st.success("Asignación guardada")
            st.rerun()

    with c2:
        if st.button("❌ Cancelar"):
            st.session_state[edit_key] = False
            st.rerun()
# -------------------------
# Exportación
# -------------------------
cur.execute("""
    SELECT
        ch.nombre AS chofer,
        COALESCE(t.id_tractor, '—') AS tractor,
        COALESCE(t.patente, '—') AS patente,
        COALESCE(t.estado, '—') AS estado_tractor
    FROM choferes ch
    LEFT JOIN tractores t ON t.id_tractor = ch.id_tractor
    WHERE ch.activo = 1
    ORDER BY ch.nombre
""")

export_rows = [dict(r) for r in cur.fetchall()]

df_export = pd.DataFrame(export_rows)

buffer = BytesIO()
df_export.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    label="📤 Exportar asignaciones Chofer–Tractor",
    data=buffer,
    file_name="chofer_tractor_asignaciones.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
