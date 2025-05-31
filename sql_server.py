import pyodbc
from datetime import datetime
import pandas as pd
import socket
import threading
from functions import CustomMessageBox as messagebox
from functions import SQLSERVER_CONFIG

class SQLServerManager:
    def __init__(self, root):
        self.root = root
        self.connection = None
        self.cursor = None
        self.servidor_activo = None
        self._mensaje_mostrado = False  # ✅ BANDERA PARA EVITAR MENSAJES REPETIDOS
        self.conectado = self.comprobar_conexion()

    def _construir_servidor(self, servidor_base):
        """Construye la cadena del servidor con puerto si está especificado."""
        if 'port' in SQLSERVER_CONFIG and SQLSERVER_CONFIG['port']:
            return f"{servidor_base},{SQLSERVER_CONFIG['port']}"
        return servidor_base

    def _test_network_connectivity(self, host, port=1433, timeout=2):
        """Prueba rápida de conectividad de red antes de intentar pyodbc."""
        try:
            if ',' in host:
                host = host.split(',')[0]
            
            socket.setdefaulttimeout(timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _probar_conexion_servidor(self, servidor):
        """Prueba optimizada con timeouts agresivos."""
        try:
            servidor_completo = self._construir_servidor(servidor)
            
            # Verificación rápida de red (2 segundos máximo)
            host_para_test = servidor_completo.split(',')[0] if ',' in servidor_completo else servidor_completo
            if not self._test_network_connectivity(host_para_test, timeout=2):
                return False, f"No hay conectividad de red con {host_para_test}"
            
            # Connection string con timeouts agresivos
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={servidor_completo};"
                f"DATABASE={SQLSERVER_CONFIG['database']};"
                f"UID={SQLSERVER_CONFIG['username']};"
                f"PWD={SQLSERVER_CONFIG['password']};"
                f"Connection Timeout=3;"
                f"Login Timeout=3;"
                f"TrustServerCertificate={SQLSERVER_CONFIG.get('trust_certificate', 'yes')};"
                f"Encrypt={SQLSERVER_CONFIG.get('encrypt', 'no')};"
            )
            
            # Conexión con timeout en thread para mayor control
            connection_result = [None, None]
            
            def try_connect():
                try:
                    conn = pyodbc.connect(connection_string)
                    cursor = conn.cursor()
                    cursor.execute("SELECT @@VERSION, @@SERVERNAME, DB_NAME()")
                    version_info = cursor.fetchone()
                    connection_result[0] = (conn, cursor, version_info)
                except Exception as e:
                    connection_result[1] = str(e)
            
            thread = threading.Thread(target=try_connect)
            thread.daemon = True
            thread.start()
            thread.join(timeout=5)
            
            if thread.is_alive():
                return False, "Timeout de conexión alcanzado (5 segundos)"
            
            if connection_result[0]:
                conn, cursor, version_info = connection_result[0]
                self.connection = conn
                self.cursor = cursor
                self.servidor_activo = servidor_completo
                return True, version_info
            else:
                return False, connection_result[1] or "Error desconocido de conexión"
                
        except Exception as e:
            return False, str(e)

    def comprobar_conexion(self):
        """Verificación rápida de conexión con fallback optimizado."""
        servidores = SQLSERVER_CONFIG.get('servers', [])
        
        if not servidores:
            return False
        
        # Probar cada servidor con timeouts cortos
        for servidor in servidores:
            exito, resultado = self._probar_conexion_servidor(servidor)
            
            if exito:
                return True
        
        # ✅ MOSTRAR ADVERTENCIA SOLO LA PRIMERA VEZ
        if not self._mensaje_mostrado:
            self._mostrar_advertencia_sin_conexion()
            self._mensaje_mostrado = True
        
        return False

    def _mostrar_advertencia_sin_conexion(self):
        """Advertencia concisa y no bloqueante."""
        mensaje = (
            "No se pudo conectar con SQL Server.\n\n"
            "La aplicación funcionará en modo sin conexión.\n\n"
            "Funciones limitadas:\n"
            "• No se actualizarán datos del servidor\n"
            "• No se podrán subir registros automáticamente"
        )
        
        try:
            messagebox.showwarning("Modo Sin Conexión", mensaje)
        except:
            pass  # Si falla el messagebox, continuar silenciosamente

    def reconectar_rapido(self):
        """Intenta reconectar rápidamente."""
        self.connection = None
        self.cursor = None
        self.servidor_activo = None
        
        servidores = SQLSERVER_CONFIG.get('servers', [])
        if servidores:
            primer_servidor = servidores[0]
            exito, _ = self._probar_conexion_servidor(primer_servidor)
            self.conectado = exito
            
            # ✅ RESETEAR BANDERA SI SE RECONECTA EXITOSAMENTE
            if exito:
                self._mensaje_mostrado = False
        
        return self.conectado

    def esta_conectado(self):
        """Verifica si la conexión actual sigue activa."""
        if not self.conectado or not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except:
            self.conectado = False
            return False

    def get_info_conexion(self):
        """Devuelve información de la conexión actual."""
        return {
            "conectado": self.conectado,
            "servidor_activo": self.servidor_activo,
            "servidores_configurados": SQLSERVER_CONFIG.get('servers', []),
            "database": SQLSERVER_CONFIG['database']
        }

    def subir_registros(self, db_manager, user_id) -> None:
        """Sube registros desde SQLite a SQL Server."""
        
        # ✅ VERIFICAR CONEXIÓN ACTUAL Y INTENTAR RECONECTAR SI ES NECESARIO
        conexion_disponible = self.esta_conectado()
        
        if not conexion_disponible:
            # Intentar reconectar antes de proceder
            conexion_disponible = self.reconectar_rapido()
        
        # Obtener registros pendientes de subir
        registros = db_manager.obtener_registros_imputando(user_id)
        
        if not registros:
            return  # No hay registros para subir
        
        # ✅ INFORMAR AL USUARIO SEGÚN EL ESTADO DE CONEXIÓN
        if not conexion_disponible:
            # Sin conexión - informar que se intentará más tarde
            mensaje = (
                f"No hay conexión con SQL Server en este momento.\n\n"
                f"Se han marcado {len(registros)} registro(s) para imputar.\n\n"
                f"Los registros se subirán automáticamente cuando "
                f"se restablezca la conexión."
            )
            messagebox.showwarning("Sin Conexión", mensaje)
            return
        
        # ✅ HAY CONEXIÓN - PROCEDER CON LA SUBIDA
        registros_subidos = 0
        registros_error = 0

        for registro in registros:
            try:
                fecha_creacion = datetime.strptime(registro["fecha_creacion"], "%Y-%m-%d %H:%M")
                fecha_imputacion = datetime.strptime(registro["fecha_imputacion"], "%Y-%m-%d %H:%M")
                
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

                # Cambiar estado a 'imputado' solo si se subió exitosamente
                db_manager.actualizar_registro(nuevos_valores={"id": registro["id"], "state": "imputado"})
                registros_subidos += 1
                
            except Exception as e:
                registros_error += 1
                # Mantener el registro como 'imputando' si falló la subida
                messagebox.showerror("Error al subir registro", 
                                f"Error subiendo registro ID {registro['id']}:\n{str(e)[:200]}")

        # ✅ RESUMEN FINAL CON INFORMACIÓN CLARA
        if registros_subidos > 0 or registros_error > 0:
            if registros_subidos > 0 and registros_error == 0:
                # Todo exitoso
                mensaje_resultado = f"✅ ¡Imputación completada!\n\n{registros_subidos} registro(s) subido(s) correctamente al servidor."
                messagebox.showinfo("Imputación Exitosa", mensaje_resultado)
            elif registros_subidos > 0 and registros_error > 0:
                # Parcialmente exitoso
                mensaje_resultado = (
                    f"⚠️ Imputación parcial:\n\n"
                    f"✅ {registros_subidos} registro(s) subido(s) correctamente\n"
                    f"❌ {registros_error} registro(s) con errores\n\n"
                    f"Los registros con errores se intentarán subir más tarde."
                )
                messagebox.showwarning("Imputación Parcial", mensaje_resultado)
            else:
                # Todo falló
                mensaje_resultado = (
                    f"❌ Error en la imputación:\n\n"
                    f"No se pudo subir ninguno de los {registros_error} registro(s).\n\n"
                    f"Se intentará nuevamente más tarde."
                )
                messagebox.showerror("Error de Imputación", mensaje_resultado)

    def ejecutar_query_personalizada(self, query):
        """Ejecuta una query personalizada y devuelve los resultados como tuplas."""
        if not self.conectado:
            messagebox.showerror("Sin conexión", 
                            "No hay conexión con SQL Server.\n"
                            "Verifique la conectividad de red.")
            return []
            
        try:
            self.cursor.execute(query)
            resultados_raw = self.cursor.fetchall()
            
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
        # ✅ NO RESETEAR LA BANDERA AQUÍ PARA EVITAR SPAM DE MENSAJES
        self.conectado = self.comprobar_conexion()
        
        return self.conectado

    def ejecutar_consulta_dataframe(self, tabla_origen, columnas_deseadas, condiciones="", orden=""):
        """Ejecuta una consulta SQL Server y devuelve un DataFrame de pandas."""
        if not self.conectado:
            return None
        
        try:
            estructura_tabla = self.obtener_estructura_tabla(tabla_origen)
            if not estructura_tabla:
                return None
            
            columnas_disponibles_en_tabla = [col[0] for col in estructura_tabla]
            columnas_validas = [col for col in columnas_deseadas if col in columnas_disponibles_en_tabla]
            
            if not columnas_validas:
                return None
            
            columnas_query = ", ".join(f"[{col}]" for col in columnas_validas)
            query = f"SELECT {columnas_query} FROM [{tabla_origen}]"
            
            if condiciones:
                query += f" WHERE {condiciones}"
            
            if orden:
                query += f" ORDER BY {orden}"
            
            self.cursor.execute(query)
            resultados_raw = self.cursor.fetchall()
            
            if not resultados_raw:
                return pd.DataFrame(columns=columnas_validas)
            
            resultados_tuplas = [tuple(row) for row in resultados_raw]
            df = pd.DataFrame(resultados_tuplas, columns=columnas_validas)
            
            if df.shape[1] != len(columnas_validas):
                return None
            
            return df
                
        except Exception as e:
            messagebox.showerror("Error de Consulta SQL Server", 
                                f"Error en consulta de tabla {tabla_origen}:\n\n{str(e)[:200]}...")
            return None

    def obtener_empleados_dataframe(self):
        """Función específica para obtener empleados activos."""
        from functions import EMPLEADOS_COLS
        
        columnas_deseadas = list(EMPLEADOS_COLS.keys())
        condiciones = "activo = 1"
        orden = "department_name, apellido_1, nombre"
        
        df = self.ejecutar_consulta_dataframe(SQLSERVER_CONFIG['empleados_tbl'], columnas_deseadas, condiciones, orden)
        
        if df is not None and not df.empty:
            if 'department_name' in df.columns:
                df = df[df['department_name'] != 'ADMINISTRACION']
            
            if df.empty:
                return pd.DataFrame()
        
        return df

    def obtener_empresas_dataframe(self):
        """Función específica para obtener empresas activas."""
        from functions import CLIENTES_COLS
        
        columnas_deseadas = list(CLIENTES_COLS.keys())
        condiciones = "baja = 0 AND vat IS NOT NULL AND vat != ''"
        orden = "name"
        
        df = self.ejecutar_consulta_dataframe(SQLSERVER_CONFIG['clientes_tbl'], columnas_deseadas, condiciones, orden)
        
        if df is not None and not df.empty:
            if 'name' in df.columns:
                df = df[df['name'].notna() & (df['name'] != '')]
            if 'vat' in df.columns:
                df = df[df['vat'].notna() & (df['vat'] != '')]
        
        return df
    
    def obtener_conceptos_dataframe(self):
        """Función específica para obtener conceptos activos."""
        from functions import CONCEPTOS_COLS
        
        columnas_deseadas = list(CONCEPTOS_COLS.keys())
        condiciones = ""
        orden = ""
        
        df = self.ejecutar_consulta_dataframe(SQLSERVER_CONFIG['conceptos_tbl'], columnas_deseadas, condiciones, orden)
        
        if df is not None and not df.empty:
            if 'Descripcion' in df.columns:
                df = df[df['Descripcion'].notna() & (df['Descripcion'] != '')]
            
            if 'Cod_concepto' in df.columns:
                df = df[df['Cod_concepto'].notna() & (df['Cod_concepto'] != '')]
        
        return df