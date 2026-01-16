from services.maestros.clientes import listar_clientes
from services.maestros.materiales import listar_materiales
from services.maestros.origenes import listar_origenes
from services.maestros.destinos import listar_destinos
from services.maestros.choferes import listar_choferes
from services.maestros.tractores import listar_tractores



def get_maestros(conn):
    return {
        "clientes": listar_clientes(conn),
        "materiales": listar_materiales(conn),
        "origenes": listar_origenes(conn),
        "destinos": listar_destinos(conn),
        "choferes": listar_choferes(conn),
        "unidades": listar_tractores(conn),   # ← clave
       # "vinculaciones": listar_vinculaciones_chofer_tractor(conn)
    }
