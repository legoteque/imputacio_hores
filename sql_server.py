import pyodbc
from datetime import datetime
import pandas as pd
from tkinter import messagebox

class SQLServerManager:
    def __init__(self, root, sqlserver_config):
        self.root = root
        self.sqlserver_config = sqlserver_config
        self.connection = None
        self.cursor = None
        conectado = self.comprobar_conexion()

    def comprobar_conexion(self):
        """Verifica la conexión a SQL Server. Si es exitosa, devuelve True y genera el cursor.
           Si falla, muestra un mensaje de error en Tkinter y devuelve False.
        """
        try:
            # Intentar conectar con SQL Server
            self.connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.sqlserver_config['server']};"
                f"DATABASE={self.sqlserver_config['database']};"
                f"UID={self.sqlserver_config['username']};"
                f"PWD={self.sqlserver_config['password']}",
                timeout=5
            )
            self.cursor = self.connection.cursor()
            #print("✅ Conexión exitosa a SQL Server.")
            return True

        except pyodbc.Error as e:
            # Crear ventana de error con Tkinter
            messagebox.showerror("Error de conexión", f"No se pudo conectar a SQL Server:\n{e}")
            #print(f"❌ Error de conexión a SQL Server: {e}")
            return False

    def subir_registros(self, db_manager, user) -> None:
        """
        Sube registros desde SQLite a SQL Server.
        """
        registros = db_manager.obtener_registros_imputando(user)
        if not registros:
            return
        
        #print(f"Subiendo {len(registros)} registros a SQL Server...")

        for registro in registros:
            # Convertir fechas a datetime antes de insertarlas en SQL Server
            fecha_creacion = datetime.strptime(registro["fecha_creacion"], "%Y-%m-%d %H:%M")
            fecha_imputacion = datetime.strptime(registro["fecha_imputacion"], "%Y-%m-%d %H:%M")
            
            insert_query = """
                INSERT INTO imputado (tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, usuario, departamento, descripcion, cif)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            valores = (
                registro["tiempo"], registro["empresa"], registro["concepto"], fecha_creacion, fecha_imputacion,
                registro["user"], registro["departamento"], registro["descripcion"], registro["cif"])

            try:
                self.cursor.execute(insert_query, valores)
                self.connection.commit()

                #print(f"Registro ID {registro['id']} subido correctamente.")

                # Actualizar estado en SQLite a 'imputado'
                db_manager.actualizar_registro(nuevos_valores={"id":registro["id"], "state": "imputado"})
            
            except pyodbc.Error as e:
                #print(f"Error insertando en SQL Server: {e}")
                pass

    def load_empleados_sql(self):
        """Carga los empleados desde SQL Server en un DataFrame de pandas."""
        query = """
            SELECT id, name, department_id, work_email, department_name 
            FROM empleados
            WHERE department_name IS NOT NULL AND department_name != 'Administration'
        """
        
        try:
            empleados_df = pd.read_sql_query(query, self.connection)
            empleados_l = empleados_df['name'].tolist()  # Lista de nombres
            return empleados_l, empleados_df
        except Exception as e:
            #print(f"Error al cargar empleados desde SQL Server: {e}")
            return [], pd.DataFrame()

    def load_empresas_sql(self):
        """Carga las empresas desde SQL Server en un DataFrame de pandas."""
        query = "SELECT id, name, vat FROM empresas"
        
        try:
            empresas_df = pd.read_sql_query(query, self.connection)
            return empresas_df
        except Exception as e:
            #print(f"Error al cargar empresas desde SQL Server: {e}")
            return pd.DataFrame()
   
    def obtener_estructura_tabla(self, tabla):
        """ Obtener estructura de la tabla en SQL Server"""
        self.cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabla}'")
        columnas = self.cursor.fetchall()
        return columnas
    
    def obtener_datos_tabla(self, tabla):
        # Obtener datos de la tabla
        self.cursor.execute(f"SELECT * FROM {tabla}")
        datos = self.cursor.fetchall()
        return datos