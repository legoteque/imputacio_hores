import sqlite3
import pandas as pd

# Conectar a la base de datos
conexion = sqlite3.connect("data/treeview_data.db")

# Cargar los datos en un DataFrame de pandas
df = pd.read_sql_query("SELECT * FROM registros", conexion)

# Ajustar configuración de Pandas para mostrar más contenido
pd.set_option("display.max_columns", None)  # Mostrar todas las columnas
pd.set_option("display.max_rows", None)  # Mostrar todas las filas
pd.set_option("display.max_colwidth", None)  # Mostrar el contenido completo de cada celda
pd.set_option("display.expand_frame_repr", False)  # Evita que Pandas divida el DataFrame en múltiples líneas

# Mostrar el DataFrame en consola
print(df)

# Cerrar conexión
conexion.close()




# import sqlite3

# db_path = "data/treeview_data.db"
# conexion = sqlite3.connect(db_path)
# cursor = conexion.cursor()

# # Intentar añadir la columna "observaciones".
# # Si la columna ya existe, se captura el error y se ignora.
# try:
#     cursor.execute("ALTER TABLE registros ADD COLUMN observaciones TEXT")
#     print("Columna 'observaciones' añadida.")
# except sqlite3.OperationalError as e:
#     if "duplicate column name" in str(e).lower():
#         print("La columna 'observaciones' ya existe.")
#     else:
#         raise

# # Actualizar todos los registros para que 'observaciones' tenga valor vacío.
# cursor.execute("UPDATE registros SET observaciones = '' WHERE observaciones IS NULL")
# conexion.commit()

# print("Todos los registros han sido actualizados con observaciones = ''.")

# conexion.close()

