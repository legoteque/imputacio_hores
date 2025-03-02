# import pyodbc

# Configuración de conexión
DB_CONFIG = {
    "server": "srv-suasor",
    "database": "INTERNA",
    "username": "conexionsql",
    "password": "conexionSQL2025"
}

# def consultar_imputado():
#     """
#     Conecta a SQL Server y muestra los registros de la tabla 'imputado'.
#     """
#     try:
#         # Crear conexión con SQL Server
#         conn = pyodbc.connect(
#             f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#             f"SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};"
#             f"UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}",
#             timeout=5
#         )
#         cursor = conn.cursor()

#         # Ejecutar consulta
#         query = "SELECT * FROM imputado"
#         cursor.execute(query)

#         # Obtener y mostrar los resultados
#         registros = cursor.fetchall()

#         if not registros:
#             print("La tabla 'imputado' está vacía.")
#         else:
#             print(f"Registros en 'imputado': {len(registros)}")
#             for row in registros:
#                 print(row)  # Muestra cada registro en formato de tupla

#         # Cerrar conexión
#         conn.close()

#     except pyodbc.Error as e:
#         print(f"Error al conectar a SQL Server o consultar la tabla: {e}")

# # Ejecutar la función
# consultar_imputado()














import pyodbc
import pandas as pd


def conectar_sql_server():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
        )
        return conn
    except pyodbc.Error as e:
        print(f"Error de conexión: {e}")
        return None

def crear_tablas():
    conn = conectar_sql_server()
    if conn:
        cursor = conn.cursor()
        
        # Verificar si la tabla 'empresas' existe antes de crearla
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='empresas' AND xtype='U')
        CREATE TABLE empresas (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            vat VARCHAR(20)
        )
        ''')
        
        # Verificar si la tabla 'empleados' existe antes de crearla
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='empleados' AND xtype='U')
        CREATE TABLE empleados (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            department_id INT,
            work_email VARCHAR(255),
            department_name VARCHAR(100)
        )
        ''')
        
        conn.commit()
        conn.close()
        print("Tablas creadas correctamente.")


def insertar_datos():
    conn = conectar_sql_server()
    if conn:
        cursor = conn.cursor()
        
        # Cargar datos desde CSV
        df_empresas = pd.read_csv(r"C:/Users/NET4/OneDrive - ETL GLOBAL/ETL/SQL Server/Imputacion Horas/data/res_partner.csv", encoding='utf-8')
        df_empleados = pd.read_csv(r"C:/Users/NET4/OneDrive - ETL GLOBAL/ETL/SQL Server/Imputacion Horas/data/hr_employee.csv", encoding='utf-8')

        # Limpiar nombres de columnas
        df_empresas.columns = df_empresas.columns.str.strip()
        df_empleados.columns = df_empleados.columns.str.strip()

        # Renombrar columnas si es necesario
        df_empresas.rename(columns={'Id': 'id'}, inplace=True)
        df_empleados.rename(columns={'Id': 'id'}, inplace=True)

        print("Columnas en empresas:", df_empresas.columns)
        print("Columnas en empleados:", df_empleados.columns)

        # Insertar datos en empresas
        for _, row in df_empresas.iterrows():
            cursor.execute('''
                INSERT INTO empresas (id, name, vat) 
                VALUES (?, ?, ?) 
            ''', row['id'], row['name'], row['vat'])
        
        # Insertar datos en empleados
        for _, row in df_empleados.iterrows():
            cursor.execute('''
                INSERT INTO empleados (id, name, department_id, work_email, department_name) 
                VALUES (?, ?, ?, ?, ?) 
            ''', row['id'], row['name'], row['department_id'], row['work_email'], row['department_name'])
        
        conn.commit()
        conn.close()
        print("Datos insertados correctamente.")


if __name__ == "__main__":
    crear_tablas()
    insertar_datos()