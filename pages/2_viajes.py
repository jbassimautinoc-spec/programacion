import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import BytesIO

from services.eventos_viaje import (
    listar_demoras_viaje,
    duracion_demoras_viaje
)
from services.viajes import (
    listar_lineas_para_viajes,
    listar_viajes,
    confirmar_linea_y_generar_viaje,
    finalizar_viaje
)
from utils.db import get_connection
from services.plantillas import listar_plantillas

# =================================================
# Configuración página
# =================================================
st.set_page_config(page_title="Viajes Operativos", layout="wide")

# =================================================
# Seguridad
# =================================================
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Tenés que iniciar sesión para acceder.")
    st.stop()

# =================================================
# Conexión
# =================================================
conn = get_connection()
st.title("🚛 Viajes Operativos")

# =================================================
# Helpers SQL (maestros)
# =================================================
def fetch_dicts(sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]

materiales = fetch_dicts("SELECT id_material, material FROM materiales WHERE activo = 1")
choferes   = fetch_dicts("SELECT id_chofer, nombre FROM choferes WHERE activo = 1")
tractores  = fetch_dicts("SELECT id_tractor, patente FROM tractores WHERE activo = 1")
clientes   = fetch_dicts("SELECT id_cliente, cliente FROM clientes")
origenes   = fetch_dicts("SELECT id_origen, origen FROM origenes")
destinos   = fetch_dicts("SELECT id_destino, destino FROM destinos")

materiales_map = {m["id_material"]: m["material"] for m in materiales}
choferes_map   = {c["id_chofer"]: c["nombre"] for c in choferes}
tractores_map  = {t["id_tractor"]: t["patente"] for t in tractores}
clientes_map   = {c["id_cliente"]: c["cliente"] for c in clientes}
origenes_map   = {o["id_origen"]: o["origen"] for o in origenes}
destinos_map   = {d["id_destino"]: d["destino"] for d in destinos}

# =================================================
# Plantillas
# =================================================
plantillas = listar_plantillas(conn)
plantillas_map = {p["id"]: p for p in plantillas}

def _get_chofer_id(linea: dict):
    return linea.get("chofer_id") or linea.get("id_chofer")

def _aplicar_plantilla(uid: str):
    pid = st.session_state.get(f"tpl_{uid}")
    if not pid:
        return
    p = plantillas_map.get(pid)
    if not p:
        return

    if p.get("id_material"):
        st.session_state[f"mat_{uid}"] = p["id_material"]
    if p.get("id_cliente") is not None:
        st.session_state[f"cli_{uid}"] = p["id_cliente"]
    if p.get("id_origen") is not None:
        st.session_state[f"ori_{uid}"] = p["id_origen"]
    if p.get("id_destino") is not None:
        st.session_state[f"des_{uid}"] = p["id_destino"]

# =================================================
# Tabs
# =================================================
tab_pend, tab_hist = st.tabs(["🟦 Pendientes (Líneas)", "🟩 Viajes generados"])

# =================================================
# TAB 1 - LÍNEAS PENDIENTES
# =================================================
with tab_pend:
    st.subheader("🟦 Líneas pendientes de generar viaje")

    c1, c2 = st.columns(2)
    with c1:
        desde_pend = st.date_input("Desde", date.today() - timedelta(days=3))
    with c2:
        hasta_pend = st.date_input("Hasta", date.today() + timedelta(days=3))

    lineas = [
        l for l in listar_lineas_para_viajes(conn)
        if desde_pend <= date.fromisoformat(l["fecha"]) <= hasta_pend
    ]

    if not lineas:
        st.info("No hay líneas pendientes.")
    else:
        for l in lineas:
            uid = f"linea_{l['id_linea']}"
            chofer_id = _get_chofer_id(l)

            titulo = (
                f"#{l['id_linea']} | {l['fecha']} | "
                f"{choferes_map.get(chofer_id, 'SIN CHOFER')} | "
                f"{l['origen_linea']}"
            )

            with st.expander(titulo):
                st.write(f"**Chofer:** {choferes_map.get(chofer_id, '—')}")
                st.write(f"**Patente:** {tractores_map.get(l.get('tractor_id'), '—')}")

                st.divider()
                st.markdown("### 📄 Plantilla de viaje")

                plantilla_id = st.selectbox(
                    "Plantilla",
                    options=[""] + list(plantillas_map.keys()),
                    format_func=lambda pid: "— Manual —" if pid == "" else plantillas_map[pid]["nombre"],
                    key=f"tpl_{uid}",
                    on_change=_aplicar_plantilla,
                    args=(uid,)
                )

                st.divider()
                st.markdown("### 📦 Datos del viaje")

                material_id = st.selectbox(
                    "Material",
                    options=[m["id_material"] for m in materiales],
                    format_func=lambda mid: materiales_map.get(mid),
                    key=f"mat_{uid}"
                )

                cliente_id = st.selectbox(
                    "Cliente",
                    options=[c["id_cliente"] for c in clientes],
                    format_func=lambda cid: clientes_map.get(cid),
                    key=f"cli_{uid}"
                )

                origen_id = st.selectbox(
                    "Origen",
                    options=[o["id_origen"] for o in origenes],
                    format_func=lambda oid: origenes_map.get(oid),
                    key=f"ori_{uid}"
                )

                destino_id = st.selectbox(
                    "Destino",
                    options=[d["id_destino"] for d in destinos],
                    format_func=lambda did: destinos_map.get(did),
                    key=f"des_{uid}"
                )

                observacion = st.text_area("Observación", key=f"obs_{uid}")

                if st.button("✅ Confirmar y generar viaje", key=f"gen_{uid}"):
                    try:
                        confirmar_linea_y_generar_viaje(
                            conn=conn,
                            id_linea=l["id_linea"],
                            origen_linea=l["origen_linea"],
                            fecha=l["fecha"],
                            chofer_id=chofer_id,
                            cliente_id=cliente_id,
                            material_id=material_id,
                            origen_id=origen_id,
                            destino_id=destino_id,
                            id_plantilla=(plantilla_id or None),
                            observacion=observacion,
                            usuario=st.session_state.user.get("email", "ui"),
                        )
                        st.success("Viaje generado")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

# =================================================
# TAB 2 - VIAJES GENERADOS
# =================================================
with tab_hist:
    st.subheader("🟩 Viajes generados")

    c1, c2 = st.columns(2)
    with c1:
        desde = st.date_input("Desde", date.today() - timedelta(days=7), key="hist_desde")
    with c2:
        hasta = st.date_input("Hasta", date.today(), key="hist_hasta")

    viajes = listar_viajes(conn, desde=str(desde), hasta=str(hasta))

    if viajes:
        df_export = pd.DataFrame([
            {
                "Fecha": v.get("fecha"),
                "Chofer": v.get("chofer"),
                "Patente": v.get("tractor"),
                "Cliente": v.get("cliente"),
                "Origen": v.get("origen"),
                "Destino": v.get("destino"),
                "Material": v.get("material"),
            }
            for v in viajes
        ])

        buffer = BytesIO()
        df_export.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "📤 Exportar viajes a Excel",
            data=buffer,
            file_name="viajes_generados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if not viajes:
        st.info("No hay viajes en el rango.")
    else:
        for v in viajes:
            viaje_id = v.get("id") or v.get("id_viaje")
            if not viaje_id:
                continue

            estado = v.get("estado", "—")
            icono_estado = {
                "CONFIRMADO": "🟢",
                "OPERATIVO": "🟡",
                "FINALIZADO": "⚪",
                "CANCELADO": "🔴",
            }.get(estado, "⚪")

            titulo = (
                f"🚛 Viaje #{viaje_id} | "
                f"{v.get('fecha', '—')} | "
                f"{v.get('chofer', '—')} | "
                f"{v.get('material', '—')} | "
                f"{icono_estado} {estado}"
            )

            with st.expander(titulo):
                st.write(f"**Chofer:** {v.get('chofer', '—')}")
                st.write(f"**Tractor:** {v.get('tractor', '—')}")
                st.write(f"**Cliente:** {v.get('cliente', '—')}")
                st.write(f"**Origen:** {v.get('origen', '—')}")
                st.write(f"**Destino:** {v.get('destino', '—')}")
                st.write(f"**Estado:** {estado}")

                st.divider()
                st.markdown("### ⏱️ Demoras del viaje")

                demoras = listar_demoras_viaje(conn, viaje_id)
                if demoras:
                    for d in demoras:
                        st.write(f"• **{d['tipo']}** | {d['inicio_ts']} → {d['fin_ts']}")
                    totales = duracion_demoras_viaje(conn, viaje_id)
                    st.caption(" | ".join(f"{k}: {v}" for k, v in totales.items()))
                else:
                    st.info("No hay demoras.")

                st.divider()
                if estado == "CONFIRMADO":
                    if st.button("✅ Finalizar viaje", key=f"fin_{viaje_id}"):
                        finalizar_viaje(conn, viaje_id, st.session_state.user.get("email", "ui"))
                        st.success("Viaje finalizado")
                        st.rerun()
                else:
                    st.info("Viaje finalizado")
