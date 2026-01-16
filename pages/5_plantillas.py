import streamlit as st

from utils.db import get_connection
from services.plantillas import listar_plantillas, crear_plantilla

# -------------------------
# Configuración
# -------------------------
st.set_page_config(page_title="Plantillas de Viaje", layout="wide")

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

st.title("📄 Plantillas de Viaje")

conn = get_connection()

# -------------------------
# Maestros
# -------------------------
def fetch(sql):
    cur = conn.cursor()
    cur.execute(sql)
    return [dict(r) for r in cur.fetchall()]

clientes = fetch("SELECT id_cliente, cliente FROM clientes WHERE activo = 1")
materiales = fetch("SELECT id_material, material FROM materiales WHERE activo = 1")
origenes = fetch("SELECT id_origen, origen FROM origenes WHERE activo = 1")
destinos = fetch("SELECT id_destino, destino FROM destinos WHERE activo = 1")

clientes_map = {c["id_cliente"]: c["cliente"] for c in clientes}
materiales_map = {m["id_material"]: m["material"] for m in materiales}
origenes_map = {o["id_origen"]: o["origen"] for o in origenes}
destinos_map = {d["id_destino"]: d["destino"] for d in destinos}

# -------------------------
# Crear plantilla
# -------------------------
st.subheader("➕ Nueva plantilla")

with st.form("form_plantilla"):

    nombre = st.text_input(
        "Nombre de la plantilla",
        placeholder="Ej: IBICUY → AÑELO | Arena"
    )

    material_id = st.selectbox(
        "Material",
        list(materiales_map.keys()),
        format_func=lambda mid: materiales_map[mid]
    )

    cliente_id = st.selectbox(
        "Cliente (opcional)",
        [""] + list(clientes_map.keys()),
        format_func=lambda cid: "—" if cid == "" else clientes_map[cid]
    )

    origen_id = st.selectbox(
        "Origen (opcional)",
        [""] + list(origenes_map.keys()),
        format_func=lambda oid: "—" if oid == "" else origenes_map[oid]
    )

    destino_id = st.selectbox(
        "Destino (opcional)",
        [""] + list(destinos_map.keys()),
        format_func=lambda did: "—" if did == "" else destinos_map[did]
    )

    observacion = st.text_area("Observación")

    submit = st.form_submit_button("Guardar plantilla")

    if submit:
        if not nombre:
            st.error("El nombre es obligatorio")
        else:
            crear_plantilla(
                conn,
                nombre=nombre,
                material_id=material_id,
                cliente_id=cliente_id or None,
                origen_id=origen_id or None,
                destino_id=destino_id or None,
                observacion=observacion,
            )
            st.success("Plantilla creada")
            st.rerun()

# -------------------------
# Listado
# -------------------------
st.divider()
st.subheader("📋 Plantillas existentes")

plantillas = listar_plantillas(conn)

if not plantillas:
    st.info("Todavía no hay plantillas creadas.")
else:
    for p in plantillas:
        with st.expander(f"📄 {p['nombre']}"):
            st.write(f"**Material:** {materiales_map.get(p['id_material'], '—')}")
            st.write(f"**Cliente:** {clientes_map.get(p['id_cliente'], '—')}")
            st.write(f"**Origen:** {origenes_map.get(p['id_origen'], '—')}")
            st.write(f"**Destino:** {destinos_map.get(p['id_destino'], '—')}")
            st.write(f"**Observación:** {p['observacion'] or '—'}")



