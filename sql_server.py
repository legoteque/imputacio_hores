import pyodbc
from datetime import datetime
import pandas as pd
from tkinter import messagebox
from functions import SQLSERVER_CONFIG

class SQLServerManager:
    def __init__(self, root):
        self.root = root
        self.connection = None
        self.cursor = None
        self.servidor_activo = None  # Servidor que funciona
        self.conectado = self.comprobar_conexion()

    def _construir_servidor(self, servidor_base):
        """Construye la cadena del servidor con puerto si está especificado."""
        # Añadir puerto si está configurado
        if 'port' in SQLSERVER_CONFIG and SQLSERVER_CONFIG['port']:
            return f"{servidor_base},{SQLSERVER_CONFIG['port']}"
        return servidor_base

    def _probar_conexion_servidor(self, servidor):
        """Prueba conectar a un servidor específico."""
        try:
            servidor_completo = self._construir_servidor(servidor)
            
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={servidor_completo};"
                f"DATABASE={SQLSERVER_CONFIG['database']};"
                f"UID={SQLSERVER_CONFIG['username']};"
                f"PWD={SQLSERVER_CONFIG['password']};"
                f"TrustServerCertificate={SQLSERVER_CONFIG.get('trust_certificate', 'yes')};"
                f"Encrypt={SQLSERVER_CONFIG.get('encrypt', 'no')};"
                f"Connection Timeout={SQLSERVER_CONFIG.get('connection_timeout', 8)}"
            )
            
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            
            # Verificar conectividad con consulta simple
            cursor.execute("SELECT @@VERSION, @@SERVERNAME, DB_NAME()")
            version_info = cursor.fetchone()
            
            # Si llegamos aquí, la conexión es exitosa
            self.connection = connection
            self.cursor = cursor
            self.servidor_activo = servidor_completo
            
            return True, version_info
            
        except pyodbc.Error as e:
            return False, str(e)

    def comprobar_conexion(self):
        """
        Verifica la conexión a SQL Server probando múltiples servidores.
        Usa sistema de fallback: dominio → IP.
        """
        servidores = SQLSERVER_CONFIG.get('servers', [])
        
        if not servidores:
            messagebox.showerror("Error de Configuración", 
                               "No hay servidores configurados en SQLSERVER_CONFIG['servers']")
            return False
        
        ultimo_error = None
        intentos_realizados = []
        
        # Probar cada servidor en orden
        for i, servidor in enumerate(servidores):
            exito, resultado = self._probar_conexion_servidor(servidor)
            intentos_realizados.append(f"{'✅' if exito else '❌'} {servidor}")
            
            if exito:
                return True
            else:
                ultimo_error = resultado
                continue
        
        # Si llegamos aquí, todos los servidores fallaron
        self._mostrar_error_fallback_completo(intentos_realizados, ultimo_error)
        return False

    def _mostrar_error_fallback_completo(self, intentos, ultimo_error):
        """Muestra error cuando todos los servidores fallan."""
        servidores_probados = "\n".join(intentos)
        
        mensaje = (
            f"❌ ERROR: TODOS LOS SERVIDORES FALLARON\n\n"
            f"🔄 Intentos realizados:\n{servidores_probados}\n\n"
            f"📋 Último error:\n{ultimo_error[:200]}...\n\n"
            f"🔧 SOLUCIONES:\n"
            f"• Verificar conectividad de red\n"
            f"• Contactar administrador de sistemas\n"
            f"• Revisar configuración de SQL Server\n"
            f"• Comprobar credenciales"
        )
        messagebox.showerror("Error de Conexión", mensaje)

    def _mostrar_error_login(self):
        """Error específico de credenciales."""
        mensaje = (
            f"❌ ERROR DE AUTENTICACIÓN\n\n"
            f"Las credenciales SQL Server son incorrectas:\n\n"
            f"👤 Usuario: {SQLSERVER_CONFIG['username']}\n"
            f"🔑 Contraseña: {'*' * len(SQLSERVER_CONFIG['password'])}\n"
            f"🗄️ Base de datos: {SQLSERVER_CONFIG['database']}\n"
            f"🌐 Servidor activo: {self.servidor_activo}\n\n"
            f"🔧 SOLUCIONES:\n"
            f"• Verificar usuario y contraseña con el administrador\n"
            f"• Comprobar si la cuenta está activa\n"
            f"• Verificar que SQL Server Authentication esté habilitado"
        )
        messagebox.showerror("Error de Credenciales", mensaje)

    def _mostrar_error_database(self):
        """Error específico de base de datos."""
        mensaje = (
            f"❌ ERROR DE BASE DE DATOS\n\n"
            f"No se puede acceder a la base de datos:\n"
            f"🗄️ '{SQLSERVER_CONFIG['database']}'\n"
            f"🌐 Servidor activo: {self.servidor_activo}\n\n"
            f"✅ Red: Funciona correctamente\n"
            f"✅ Credenciales: Probablemente correctas\n\n"
            f"🔧 POSIBLES CAUSAS:\n"
            f"• La base de datos no existe\n"
            f"• Sin permisos de acceso a esta BD específica\n"
            f"• Base de datos en modo mantenimiento\n"
            f"• Nombre de BD incorrecto"
        )
        messagebox.showerror("Error de Base de Datos", mensaje)

    def get_info_conexion(self):
        """Devuelve información de la conexión actual."""
        return {
            "conectado": self.conectado,
            "servidor_activo": self.servidor_activo,
            "servidores_configurados": SQLSERVER_CONFIG.get('servers', []),
            "database": SQLSERVER_CONFIG['database']
        }

    def subir_registros(self, db_manager, user) -> None:
        """Sube registros desde SQLite a SQL Server."""
        if not self.conectado:
            messagebox.showwarning("Sin conexión", 
                                 "No hay conexión con SQL Server.\n"
                                 "No se pueden subir registros.")
            return

        registros = db_manager.obtener_registros_imputando(user)
        if not registros:
            return

        registros_subidos = 0
        registros_error = 0

        for registro in registros:
            try:
                # Convertir fechas a datetime
                fecha_creacion = datetime.strptime(registro["fecha_creacion"], "%Y-%m-%d %H:%M")
                fecha_imputacion = datetime.strptime(registro["fecha_imputacion"], "%Y-%m-%d %H:%M")
                
                # Insertar en tabla de imputaciones
                tabla_imputaciones = SQLSERVER_CONFIG['imputaciones_tbl']
                insert_query = f"""
                    INSERT INTO {tabla_imputaciones} 
                    (tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, usuario, departamento, descripcion, cif)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                valores = (
                    registro["tiempo"], registro["empresa"], registro["concepto"], 
                    fecha_creacion, fecha_imputacion, registro["user"], 
                    registro["departamento"], registro["descripcion"], registro["cif"]
                )

                self.cursor.execute(insert_query, valores)
                self.connection.commit()

                # Actualizar estado en SQLite a 'imputado'
                db_manager.actualizar_registro(nuevos_valores={"id": registro["id"], "state": "imputado"})
                registros_subidos += 1
                
            except pyodbc.Error as e:
                registros_error += 1
                messagebox.showerror("Error al subir registro", 
                                   f"Error subiendo registro ID {registro['id']}:\n{str(e)[:200]}")

        # Resumen final solo cuando hay registros subidos
        if registros_subidos > 0:
            mensaje_resultado = f"✅ {registros_subidos} registros subidos correctamente"
            if registros_error > 0:
                mensaje_resultado += f"\n❌ {registros_error} registros con error"
            
            messagebox.showinfo("Registros subidos", mensaje_resultado)

    def ejecutar_query_personalizada(self, query):
        """
        Ejecuta una query personalizada y devuelve los resultados como tuplas.
        FIX: Convierte pyodbc.Row a tuplas automáticamente.
        """
        if not self.conectado:
            messagebox.showerror("Sin conexión", 
                            "No hay conexión con SQL Server.\n"
                            "Verifique la conectividad de red.")
            return []
            
        try:
            self.cursor.execute(query)
            resultados_raw = self.cursor.fetchall()
            
            # Convertir pyodbc.Row a tuplas
            if resultados_raw and hasattr(resultados_raw[0], '__iter__'):
                resultados = [tuple(row) for row in resultados_raw]
            else:
                resultados = resultados_raw
            
            return resultados
            
        except Exception as e:
            messagebox.showerror("Error de Consulta", 
                                f"Error ejecutando consulta:\n\n{str(e)[:300]}")
            return []

    def obtener_estructura_tabla(self, tabla):
        """Obtiene estructura de la tabla en SQL Server."""
        if not self.conectado:
            return []
            
        try:
            query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabla}'"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except:
            return []
    
    def obtener_datos_tabla(self, tabla):
        """Obtiene datos de la tabla."""
        if not self.conectado:
            return []
            
        try:
            self.cursor.execute(f"SELECT * FROM {tabla}")
            return self.cursor.fetchall()
        except:
            return []

    def reconectar(self):
        """Intenta reconectar usando el sistema de fallback."""
        self.connection = None
        self.cursor = None
        self.servidor_activo = None
        self.conectado = self.comprobar_conexion()
        
        return self.conectado

    def ejecutar_consulta_dataframe(self, tabla_origen, columnas_deseadas, condiciones="", orden=""):
        """
        Ejecuta una consulta SQL Server y devuelve un DataFrame de pandas.
        Solo muestra errores cuando algo falla.
        """
        if not self.conectado:
            return None
        
        try:
            # Verificar estructura de la tabla
            estructura_tabla = self.obtener_estructura_tabla(tabla_origen)
            if not estructura_tabla:
                return None
            
            columnas_disponibles_en_tabla = [col[0] for col in estructura_tabla]
            
            # Filtrar solo las columnas que existen
            columnas_validas = [col for col in columnas_deseadas if col in columnas_disponibles_en_tabla]
            
            if not columnas_validas:
                return None
            
            # Construir query de forma segura
            columnas_query = ", ".join(f"[{col}]" for col in columnas_validas)
            query = f"SELECT {columnas_query} FROM [{tabla_origen}]"
            
            if condiciones:
                query += f" WHERE {condiciones}"
            
            if orden:
                query += f" ORDER BY {orden}"
            
            # Ejecutar consulta
            self.cursor.execute(query)
            resultados_raw = self.cursor.fetchall()
            
            if not resultados_raw:
                return pd.DataFrame(columns=columnas_validas)
            
            # Convertir a DataFrame
            resultados_tuplas = [tuple(row) for row in resultados_raw]
            df = pd.DataFrame(resultados_tuplas, columns=columnas_validas)
            
            # Verificar integridad del DataFrame
            if df.shape[1] != len(columnas_validas):
                return None
            
            return df
                
        except Exception as e:
            messagebox.showerror("Error de Consulta SQL Server", 
                                f"Error en consulta de tabla {tabla_origen}:\n\n{str(e)[:200]}...")
            return None

    def obtener_empleados_dataframe(self):
        """
        Función específica para obtener empleados activos.
        """
        from functions import EMPLEADOS_COLS
        
        columnas_deseadas = list(EMPLEADOS_COLS.keys())
        condiciones = "activo = 1"
        orden = "department_name, apellido_1, nombre"
        
        df = self.ejecutar_consulta_dataframe(SQLSERVER_CONFIG['empleados_tbl'], columnas_deseadas, condiciones, orden)
        
        # Validaciones específicas para empleados
        if df is not None and not df.empty:
            # Filtrar empleados de departamento distinto a ADMINISTRACION
            if 'department_name' in df.columns:
                df = df[df['department_name'] != 'ADMINISTRACION']
            
            # Validar que hay empleados después del filtro
            if df.empty:
                return pd.DataFrame()
        
        return df

    def obtener_empresas_dataframe(self):
        """
        Función específica para obtener empresas activas.
        """
        from functions import CLIENTES_COLS
        
        columnas_deseadas = list(CLIENTES_COLS.keys())
        condiciones = "baja = 0 AND vat IS NOT NULL AND vat != ''"
        orden = "name"
        
        df = self.ejecutar_consulta_dataframe(SQLSERVER_CONFIG['clientes_tbl'], columnas_deseadas, condiciones, orden)
        
        # Validaciones específicas para empresas
        if df is not None and not df.empty:
            # Limpiar datos si es necesario
            if 'name' in df.columns:
                df = df[df['name'].notna() & (df['name'] != '')]
            if 'vat' in df.columns:
                df = df[df['vat'].notna() & (df['vat'] != '')]
        
        return df