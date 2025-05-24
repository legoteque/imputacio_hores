import sqlite3
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from functions import EMPLEADOS_COLS, CLIENTES_COLS, REGISTRO_COLS

TABLA_REGISTROS = "registros"

class DatabaseManager:
    def __init__(self, app, db_path: str) -> None:
        self.app = app
        self.db_path = db_path
        self.columnas = REGISTRO_COLS.copy()
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        self._crear_tabla()


    def _crear_tabla(self) -> None:
        """
        Crea la tabla en SQLite si no existe, utilizando la definición de columnas.
        """
        columnas_sql = ",\n".join(f"{col} {tipo}" for col, tipo in self.columnas.items())
        query = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_REGISTROS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {columnas_sql}
            )
        """
        self.cursor.execute(query)
        self.conexion.commit()



    def sincronizar_empleados(self):
        """
        Versión mejorada con mejor manejo de errores y rollback.
        """
        if not self.app.sql_server_manager.comprobar_conexion():
            return False
        
        # Iniciar transacción
        try:
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Obtener DataFrame desde SQL Server
            df_empleados = self.app.sql_server_manager.obtener_empleados_dataframe()
            
            if df_empleados is None:
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showerror("Error de Consulta", 
                                "No se pudo ejecutar la consulta de empleados en SQL Server")
                return False
            
            if df_empleados.empty:
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showwarning("Sin Datos", 
                                    "No se encontraron empleados activos en la base de datos.")
                return False
            
            # Validar estructura antes de guardar
            columnas_esperadas = set(EMPLEADOS_COLS.keys())
            columnas_recibidas = set(df_empleados.columns)
            
            if not columnas_esperadas.issubset(columnas_recibidas):
                columnas_faltantes = columnas_esperadas - columnas_recibidas
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showerror("Error de Estructura", 
                                f"Faltan columnas esperadas: {list(columnas_faltantes)}")
                return False
            
            # Guardar en SQLite (reemplaza tabla completa)
            df_empleados.to_sql(
                name="empleados",
                con=self.conexion,
                if_exists='replace',
                index=False,
                method='multi'
            )
            
            # Confirmar transacción
            self.conexion.commit()
            return True
            
        except Exception as e:
            # Rollback en caso de error
            self.conexion.rollback()
            from tkinter import messagebox
            messagebox.showerror("Error de Sincronización", 
                            f"Error al sincronizar empleados:\n\n{str(e)[:200]}...")
            return False

    def sincronizar_empresas(self):
        """
        Versión mejorada con mejor manejo de filtros y transacciones.
        """
        if not self.app.sql_server_manager.comprobar_conexion():
            return False
        
        # Iniciar transacción
        try:
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Obtener DataFrame desde SQL Server
            df_empresas = self.app.sql_server_manager.obtener_empresas_dataframe()
            
            if df_empresas is None:
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showerror("Error de Consulta", 
                                "No se pudo ejecutar la consulta de empresas en SQL Server")
                return False
            
            if df_empresas.empty:
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showwarning("Sin Datos", 
                                    "No se encontraron empresas activas en la base de datos.")
                return False
            
            # Aplicar filtros de forma más robusta
            df_final = self._aplicar_filtros_empresas(df_empresas)
            
            if df_final.empty:
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showwarning("Sin Datos Filtrados", 
                                    "No se encontraron empresas después de aplicar los filtros de origen.")
                return False
            
            # Validar estructura antes de guardar
            columnas_esperadas = set(CLIENTES_COLS.keys())
            columnas_recibidas = set(df_final.columns)
            
            if not columnas_esperadas.issubset(columnas_recibidas):
                columnas_faltantes = columnas_esperadas - columnas_recibidas
                self.conexion.rollback()
                from tkinter import messagebox
                messagebox.showerror("Error de Estructura", 
                                f"Faltan columnas esperadas: {list(columnas_faltantes)}")
                return False
            
            # Guardar en SQLite
            df_final.to_sql(
                name="empresas",
                con=self.conexion,
                if_exists='replace',
                index=False,
                method='multi'
            )
            
            # Confirmar transacción
            self.conexion.commit()
            return True
            
        except Exception as e:
            # Rollback en caso de error
            self.conexion.rollback()
            from tkinter import messagebox
            messagebox.showerror("Error de Sincronización", 
                            f"Error al sincronizar empresas:\n\n{str(e)[:200]}...")
            return False

    def _aplicar_filtros_empresas(self, df_empresas):
        """
        Método separado para aplicar filtros de empresas de forma más clara.
        """
        # Verificar que existen las columnas necesarias para filtrar
        if 'origen' not in df_empresas.columns or 'name' not in df_empresas.columns:
            # Si no existen las columnas de filtro, devolver todos los datos
            return df_empresas.copy()
        
        try:
            # Aplicar filtros por origen
            mask_otros = df_empresas['origen'].str.contains('otros', case=False, na=False)
            mask_cero = df_empresas['name'].str.startswith('0', na=False)
            df_otros = df_empresas[mask_otros & mask_cero]
            
            mask_suasor = df_empresas['origen'].str.contains('suasor', case=False, na=False)
            df_suasor = df_empresas[mask_suasor]
            
            mask_lexon = df_empresas['origen'].str.contains('lexon', case=False, na=False)
            df_lexon = df_empresas[mask_lexon]
            
            # Combinar todos los filtros
            dataframes_filtrados = [df for df in [df_otros, df_suasor, df_lexon] if not df.empty]
            
            if dataframes_filtrados:
                df_final = pd.concat(dataframes_filtrados, ignore_index=True)
                # Eliminar duplicados si los hay
                df_final = df_final.drop_duplicates(subset=['vat'], keep='first')
            else:
                df_final = pd.DataFrame()
            
            return df_final
            
        except Exception as e:
            print(f"⚠️ Error aplicando filtros de empresas: {e}")
            # En caso de error en filtros, devolver datos sin filtrar
            return df_empresas.copy()

    # FUNCIÓN ADICIONAL: Sincronización con retry
    def sincronizar_con_reintentos(self, max_intentos=3):
        """
        Sincronización con sistema de reintentos en caso de fallo.
        """
        for intento in range(1, max_intentos + 1):
            try:
                # Intentar reconectar si no hay conexión
                if not self.app.sql_server_manager.conectado:
                    if not self.app.sql_server_manager.reconectar():
                        if intento == max_intentos:
                            from tkinter import messagebox
                            messagebox.showerror("Error de Conexión", 
                                            "No se pudo establecer conexión con SQL Server después de varios intentos.")
                            return False
                        continue
                
                # Intentar sincronizar empleados
                empleados_ok = self.sincronizar_empleados()
                
                # Intentar sincronizar empresas
                empresas_ok = self.sincronizar_empresas()
                
                if empleados_ok and empresas_ok:
                    return True
                elif intento == max_intentos:
                    from tkinter import messagebox
                    resultado_empleados = "✅" if empleados_ok else "❌"
                    resultado_empresas = "✅" if empresas_ok else "❌"
                    messagebox.showwarning("Sincronización Parcial", 
                                        f"Resultados de sincronización:\n"
                                        f"{resultado_empleados} Empleados\n"
                                        f"{resultado_empresas} Empresas")
                    return empleados_ok or empresas_ok
                
            except Exception as e:
                if intento == max_intentos:
                    from tkinter import messagebox
                    messagebox.showerror("Error de Sincronización", 
                                    f"Error en sincronización (intento {intento}):\n{str(e)[:200]}...")
                    return False
                
                # Pequeña pausa antes del siguiente intento
                import time
                time.sleep(1)
        
        return False




    def load_empleados_sqlite(self):
        """Carga los empleados desde SQLite en un DataFrame de pandas."""
        query = """
            SELECT id, nombre, apellido_1, department_name 
            FROM empleados
            WHERE department_name IS NOT NULL AND department_name != 'ADMINISTRACION' AND activo = 1;
        """
        
        try:
            self.cursor.execute(query)
            empleados_data = self.cursor.fetchall()
            empleados_df = pd.DataFrame(empleados_data, columns=[col[0] for col in self.cursor.description])
            empleados_df['name'] = empleados_df['nombre'] + " " + empleados_df['apellido_1']
            empleados_dict = dict(zip(empleados_df['name'], empleados_df['id']))
            return empleados_dict, empleados_df
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Error al cargar empleados desde SQLite:\n{e}")
            return {}, pd.DataFrame()

    def load_empresas_sqlite(self):
        """Carga las empresas desde SQLite en un DataFrame de pandas."""
        query = "SELECT name, vat FROM empresas WHERE baja = 0"  # Solo empresas activas
        
        try:
            self.cursor.execute(query)
            empresas_data = self.cursor.fetchall()
            empresas_df = pd.DataFrame(empresas_data, columns=[col[0] for col in self.cursor.description])
            return empresas_df
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Error al cargar empresas desde SQLite:\n{e}")
            return pd.DataFrame()

    def obtener_registros(self, user: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros de un usuario específico con estado 'working'.
        Solo se devuelven los campos que se muestran en el treeview.
        """
        query = f"""
            SELECT id, tiempo, empresa, concepto, fecha_creacion
            FROM {TABLA_REGISTROS}
            WHERE state = 'working' AND user = ?
        """
        self.cursor.execute(query, (user,))
        registros = self.cursor.fetchall()
        columnas = ["id", "tiempo", "empresa", "concepto", "fecha_creacion"]
        return [dict(zip(columnas, row)) for row in registros]

    def agregar_registro(self, tiempo: int, register_dic: dict, user: str, departamento: str):
        """
        Agrega un nuevo registro a la base de datos, desempaquetando los valores del diccionario.

        :param tiempo: Valor del tiempo.
        :param register_dic: Diccionario con los valores de 'empresa', 'concepto' y opcionalmente 'descripcion'.
        :param user: Nombre del usuario que realiza el registro.
        :param departamento: Departamento al que pertenece el usuario.
        :return: ID del registro insertado.
        """
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Extraer valores del diccionario con valores predeterminados
        empresa = register_dic.get("empresa", "")
        concepto = register_dic.get("concepto", "")
        descripcion = register_dic.get("descripcion", "")

        query = f"""
            INSERT INTO {TABLA_REGISTROS} (tiempo, empresa, concepto, fecha_creacion, state, user, departamento, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.cursor.execute(query, (tiempo, empresa, concepto, fecha_creacion, "working", user, departamento, descripcion))
        self.conexion.commit()
        return str(self.cursor.lastrowid)

    def obtener_registro(self, registro_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro de la base de datos por su ID y devuelve un diccionario con columna: valor.
        Se incluye el campo 'descripcion'.
        """
        query = f"""
            SELECT id, {", ".join(self.columnas.keys())}
            FROM {TABLA_REGISTROS}
            WHERE id = ?
        """
        self.cursor.execute(query, (registro_id,))
        registro = self.cursor.fetchone()
        if registro:
            columnas_lista = ["id"] + list(self.columnas.keys())
            return dict(zip(columnas_lista, registro))
        return None

    def obtener_empresas_temporales(self):
        """
        Extrae un diccionario {empresa: cif} con valores únicos de todas las empresas 
        cuyo campo vinculada sea False (0) en la base de datos SQLite.
        
        :return: Diccionario con empresas no vinculadas y sus respectivos CIF.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Consultar las empresas no vinculadas (vinculada = 0) y filtradas por usuario
        cursor.execute("SELECT DISTINCT empresa, cif FROM registros WHERE vinculada = 0 AND user = ? AND state = 'working'",
                       (self.app.session.user,))
        empresas_no_vinculadas = cursor.fetchall()

        # Convertir a diccionario
        empresas_temporales = {empresa.upper(): cif.upper() if cif is not None else None for empresa, cif in empresas_no_vinculadas}
        conn.close()
        return empresas_temporales

    def actualizar_registro(self, nuevos_valores: Optional[Dict[str, Any]] = None, tiempo: Optional[str] = None) -> None:
        """
        Actualiza un registro en la base de datos con los nuevos valores, solo el tiempo o ambos.
        Se contempla el campo 'descripcion' si se incluye en nuevos_valores.
        """
        if nuevos_valores is None:
            return

        registro_id = nuevos_valores["id"]

        if nuevos_valores or tiempo is not None:
            columnas_actualizar = []
            valores = []
            
            if nuevos_valores:
                columnas_actualizar.extend([col for col in nuevos_valores.keys() if col in self.columnas])
                valores.extend([nuevos_valores[col] for col in columnas_actualizar])
            
            if tiempo is not None:
                columnas_actualizar.append("tiempo")
                valores.append(tiempo)
            
            set_clause = ", ".join(f"{col} = ?" for col in columnas_actualizar)
            valores.append(registro_id)
            query = f"UPDATE {TABLA_REGISTROS} SET {set_clause} WHERE id = ?"
            self.cursor.execute(query, valores)
        else:
            raise ValueError("Debe proporcionar nuevos valores, un tiempo a actualizar o ambos.")
    
        self.conexion.commit()

    def obtener_registros_imputando(self, usuario):
        """
        Obtiene registros con state = 'imputando' para ser subidos a SQL Server por dicho usuario.
        """        
        query = f"SELECT id, {', '.join(self.columnas.keys())} FROM {TABLA_REGISTROS} WHERE state = ? AND user = ?"
        self.cursor.execute(query, ('imputando', usuario))

        registros = self.cursor.fetchall()
        
        # Incluir `id` en el diccionario resultante
        columnas = ["id"] + list(self.columnas.keys())
        return [dict(zip(columnas, row)) for row in registros]

    def vincular_empresa(self, empresa_anterior: str, empresa_real: str, cif_real: str) -> None:
        """
        Reemplaza todos los registros donde la empresa sea 'empresa_anterior' con 'empresa_real'.
        Obtiene el CIF de 'empresa_real' y establece 'vinculada' en 1.

        :param empresa_anterior: Nombre de la empresa a reemplazar.
        :param empresa_real: Nombre de la empresa que sustituirá a la anterior.
        :param cif_real: Nombre del cif de la empresa que sustituirá a la anterior.
        """
        # Actualizar registros que contengan la empresa anterior
        query_actualizar = f"""
            UPDATE {TABLA_REGISTROS}
            SET empresa = ?, cif = ?, vinculada = 1
            WHERE empresa = ?
        """
        self.cursor.execute(query_actualizar, (empresa_real, cif_real, empresa_anterior))
        self.conexion.commit()

    def borrar_registro(self, registro_id: int) -> None:
        """
        Borra un registro de la base de datos.
        """
        self.cursor.execute(f"DELETE FROM {TABLA_REGISTROS} WHERE id = ?", (registro_id,))
        self.conexion.commit()

    def cerrar_conexion(self) -> None:
        """
        Cierra la conexión con la base de datos.
        """
        self.conexion.close()

    def __del__(self) -> None:
        try:
            self.cerrar_conexion()
        except Exception:
            pass