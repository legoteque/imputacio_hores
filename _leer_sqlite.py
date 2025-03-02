import sqlite3
import pandas as pd
from functions import DB_PATH

# Conectar a la base de datos
conexion = sqlite3.connect(DB_PATH)

# Cargar los datos en un DataFrame de pandas
df = pd.read_sql_query("SELECT * FROM empresas", conexion)

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
# import pandas as pd

# # Conectar a la base de datos
# conexion = sqlite3.connect("data/treeview_data.db")
# cursor = conexion.cursor()

# # Verificar si la columna 'observaciones' existe en la tabla 'registros'
# cursor.execute("PRAGMA table_info(registros);")
# columnas = [col[1] for col in cursor.fetchall()]

# if 'observaciones' in columnas:
#     # Renombrar la columna 'observaciones' a 'descripcion'
#     cursor.execute("ALTER TABLE registros RENAME COLUMN observaciones TO descripcion;")
#     print("Columna 'observaciones' renombrada a 'descripcion' correctamente.")
# else:
#     print("La columna 'observaciones' no existe en la tabla 'registros'.")

# # Confirmar cambios y cerrar conexión
# conexion.commit()
# conexion.close()
