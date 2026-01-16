# core/reglas.py
# =================================================
# Reglas del sistema BCA
# =================================================

# -------------------------
# Estados válidos
# -------------------------
ESTADOS_VIAJE = [
    "PROGRAMADO",
    "CONFIRMADO",
    "CANCELADO"
]


# -------------------------
# Reglas sobre viajes
# -------------------------
def se_puede_editar_viaje(estado_viaje: str) -> bool:
    """
    Un viaje solo se puede editar si está PROGRAMADO.
    """
    return estado_viaje == "PROGRAMADO"


def se_puede_cancelar_viaje(estado_viaje: str) -> bool:
    """
    Un viaje se puede cancelar si no está ya cancelado.
    """
    return estado_viaje != "CANCELADO"


# -------------------------
# Reglas sobre choferes
# -------------------------
def chofer_esta_disponible(en_franco: bool, tiene_viaje_asignado: bool) -> bool:
    """
    Un chofer está disponible si:
    - no está en franco
    - no tiene viaje asignado
    """
    return not en_franco and not tiene_viaje_asignado


# -------------------------
# Reglas sobre tractores
# -------------------------
def tractor_esta_disponible(en_mantenimiento: bool, tiene_chofer: bool) -> bool:
    """
    Un tractor está disponible si:
    - no está en mantenimiento
    - no está asignado a otro chofer
    """
    return not en_mantenimiento and not tiene_chofer

    
def se_puede_operar_viaje(estado_viaje: str) -> bool:
    """
    Un viaje se puede confirmar o cancelar
    solo si está en estado PENDIENTE.
    """
    return estado_viaje == "PENDIENTE"
