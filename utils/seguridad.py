# utils/seguridad.py

import streamlit as st

def require_roles(*roles):
    """
    Bloquea acceso si el usuario no tiene alguno de los roles permitidos.
    ADMIN y GERENTE siempre deben estar explícitos si querés acceso total.
    """
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Tenés que iniciar sesión.")
        st.stop()

    rol = st.session_state.user.get("rol")

    if rol not in roles:
        st.error("No tenés permisos para acceder a este módulo.")
        st.stop()
        
if st.session_state.user["rol"] not in (
    "ADMIN", "GERENTE", "MONITOREO", "TRAFICO", "PROGRAMACION"
):
    st.error("No tenés permisos para ver la Agenda.")
    st.stop()
