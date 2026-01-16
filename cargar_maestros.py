from utils.db import get_connection
from services.maestros.choferes import importar_si_cambio as importar_choferes
from services.maestros.materiales import importar_si_cambio as importar_materiales

conn = get_connection()

print(importar_choferes(conn, "data/excels/Base_Choferes.xlsx"))
print(importar_materiales(conn, "data/excels/Base_Materiales.xlsx"))

conn.close()
