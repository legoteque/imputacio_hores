import sqlite3
import pandas as pd

# Conectar a la base de datos
conexion = sqlite3.connect("data/treeview_data.db")

# Cargar los datos en un DataFrame de pandas
df = pd.read_sql_query("SELECT * FROM registros WHERE user = 'DEBORA MACIAS'", conexion)

# Mostrar el DataFrame
print(df)

# Cerrar conexión
conexion.close()

