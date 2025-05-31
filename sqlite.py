import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from functions import EMPLEADOS_COLS, CLIENTES_COLS, REGISTRO_COLS
from functions import CustomMessageBox as messagebox

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
                messagebox.showerror("Error de Consulta", 
                                "No se pudo ejecutar la consulta de empleados en SQL Server")
                return False
            
            if df_empleados.empty:
                self.conexion.rollback()
                messagebox.showwarning("Sin Datos", 
                                    "No se encontraron empleados activos en la base de datos.")
                return False
            
            # Validar estructura antes de guardar
            columnas_esperadas = set(EMPLEADOS_COLS.keys())
            columnas_recibidas = set(df_empleados.columns)
            
            if not columnas_esperadas.issubset(columnas_recibidas):
                columnas_faltantes = columnas_esperadas - columnas_recibidas
                self.conexion.rollback()
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
                messagebox.showerror("Error de Consulta", 
                                "No se pudo ejecutar la consulta de empresas en SQL Server")
                return False
            
            if df_empresas.empty:
                self.conexion.rollback()
                messagebox.showwarning("Sin Datos", 
                                    "No se encontraron empresas activas en la base de datos.")
                return False
            
            # Aplicar filtros de forma más robusta
            df_final = self._aplicar_filtros_empresas(df_empresas)
            
            if df_final.empty:
                self.conexion.rollback()
                messagebox.showwarning("Sin Datos Filtrados", 
                                    "No se encontraron empresas después de aplicar los filtros de origen.")
                return False
            
            # Validar estructura antes de guardar
            columnas_esperadas = set(CLIENTES_COLS.keys())
            columnas_recibidas = set(df_final.columns)
            
            if not columnas_esperadas.issubset(columnas_recibidas):
                columnas_faltantes = columnas_esperadas - columnas_recibidas
                self.conexion.rollback()
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
            messagebox.showerror("Error de Sincronización", 
                            f"Error al sincronizar empresas:\n\n{str(e)[:200]}...")
            return False


    def sincronizar_conceptos(self):
        """
        Sincroniza conceptos desde SQL Server a SQLite.
        """
        if not self.app.sql_server_manager.comprobar_conexion():
            return False
        
        # Iniciar transacción
        try:
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Obtener DataFrame desde SQL Server
            df_conceptos = self.app.sql_server_manager.obtener_conceptos_dataframe()
            
            if df_conceptos is None:
                self.conexion.rollback()
                messagebox.showerror("Error de Consulta", 
                                "No se pudo ejecutar la consulta de conceptos en SQL Server")
                return False
            
            if df_conceptos.empty:
                self.conexion.rollback()
                messagebox.showwarning("Sin Datos", 
                                    "No se encontraron conceptos en la base de datos.")
                return False
            
            # Validar estructura antes de guardar
            from functions import CONCEPTOS_COLS
            columnas_esperadas = set(CONCEPTOS_COLS.keys())
            columnas_recibidas = set(df_conceptos.columns)
            
            if not columnas_esperadas.issubset(columnas_recibidas):
                columnas_faltantes = columnas_esperadas - columnas_recibidas
                self.conexion.rollback()
                messagebox.showerror("Error de Estructura", 
                                f"Faltan columnas esperadas en conceptos: {list(columnas_faltantes)}")
                return False
            
            # Guardar en SQLite (reemplaza tabla completa)
            df_conceptos.to_sql(
                name="conceptos",
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
            messagebox.showerror("Error de Sincronización", 
                            f"Error al sincronizar conceptos:\n\n{str(e)[:200]}...")
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
            # En caso de error en filtros, devolver datos sin filtrar
            return df_empresas.copy()



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
            messagebox.showerror("Error", f"Error al cargar empresas desde SQLite:\n{e}")
            return pd.DataFrame()
        
    def load_conceptos_sqlite(self):
        """Carga los conceptos desde SQLite en un DataFrame de pandas."""
        
        # Obtener el departamento del usuario desde session_manager
        department = self.app.session.department
        
        # Si no hay departamento, devolver DataFrame vacío
        if not department:
            return pd.DataFrame()
        
        # Construir la query con filtro por departamento
        # Si el departamento es FISCAL, incluir también CONTABILIDAD
        if department == "FISCAL":
            query = "SELECT [Cod_ concepto], [Descripcion] FROM conceptos WHERE [Cod_ modulo] IN ('FISCAL', 'CONTABILIDAD')"
        else:
            query = "SELECT [Cod_ concepto], [Descripcion] FROM conceptos WHERE [Cod_ modulo] = ?"
        
        try:
            if department == "FISCAL":
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, (department,))
                
            conceptos_data = self.cursor.fetchall()
            conceptos_df = pd.DataFrame(conceptos_data, columns=[col[0] for col in self.cursor.description])
            
            return conceptos_df
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar conceptos desde SQLite:\n{e}")
            return pd.DataFrame()

    def obtener_registros(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene registros de un usuario específico con las siguientes reglas:
        - TODOS los registros 'working' (sin importar la fecha)
        - Solo registros 'imputado'/'imputando' del mes actual y mes anterior
        
        Los resultados se ordenan para mostrar primero los 'working' y luego los otros por fecha.
        """
        from datetime import datetime
        
        # Calcular fechas límite
        fecha_actual = datetime.now()
        año_actual = fecha_actual.year
        mes_actual = fecha_actual.month
        
        # Calcular mes anterior
        if mes_actual == 1:
            mes_anterior = 12
            año_mes_anterior = año_actual - 1
        else:
            mes_anterior = mes_actual - 1
            año_mes_anterior = año_actual
        
        # Crear fechas límite (primer día del mes anterior)
        fecha_limite_inferior = f"{año_mes_anterior:04d}-{mes_anterior:02d}-01"
        
        query = f"""
            SELECT id, tiempo, empresa, concepto, fecha_creacion, state
            FROM {TABLA_REGISTROS}
            WHERE user = ? 
            AND (
                state = 'working' 
                OR (
                    state IN ('imputado', 'imputando') 
                    AND fecha_creacion >= ?
                )
            )
            ORDER BY 
                CASE 
                    WHEN state = 'working' THEN 0 
                    ELSE 1 
                END,
                fecha_creacion DESC
        """
        
        self.cursor.execute(query, (user_id, fecha_limite_inferior))
        registros = self.cursor.fetchall()
        columnas = ["id", "tiempo", "empresa", "concepto", "fecha_creacion", "state"]
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
        resultado = [dict(zip(columnas, row)) for row in registros]

        return resultado

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



    def sqlite_update_to_new_version(self) -> bool:
        """
        Reemplaza en TABLA_REGISTROS cada user (nombre) por su ID según el mapeo hardcodeado,
        y borra el valor de 'concepto' en todos los registros con state = 'working'.
        
        :return: True si todo OK, False si hubo error.
        """
        # Diccionario de mapeo nombre -> id para la actualización
        empleados_mapping = {
            "MAITE ROVIRA FALCO": "000005",
            "EVELYNE GONZALEZ LOPEZ": "000013", 
            "ALBERT NOGUERA MIRAS": "000023",
            "CARMEN ALONSO": "000031",
            "MONICA SANCHEZ ZAMBRANA": "000034",
            "ALEJANDRO DE LOS SANTOS": "000039",
            "RAQUEL PRAT SILES": "000044",
            "BERTHA GARCIA": "000045",
            "MONICA TRILLO PALMERO": "000048",
            "LAURENCE BOYER": "000050",
            "LUCIANA MARTIN ETKIN": "000054",
            "SUSANA NOLLA": "000062",
            "ORIOL ALVAREZ MARSAL": "000063",
            "ERIC TALABARDON": "000064",
            "SUSANA COLOM ARMENGOL": "000065",
            "OSCAR BOADELLA RABES": "000066",
            "GERARD NAVARRO": "000067",
            "ROSA RAMOS MERCADO": "000069",
            "MARIA ACEBO": "000070",
            "MA ANGELES LAVADO RICART": "000071",
            "INES KEBAILI GARCIA": "000072",
            "CLARA BARNES": "000073",
            "DEBORA MACIAS": "000074",
            "SILVIA MATAS GARCIA": "000075",
            "MARTA AROYO": "000076",
            "ANA VIDAO": "000077",
            "JON LOPEZ": "000078",
            "GABRIELA ALDUNATE": "000079",
            "OSCAR TORRES VERGES": "000081",
            "OSCAR TORRES": "000081",
            "JUAN MANUEL GONZALEZ": "000083",
            "LAURA BAEZA": "000084",
            "MARIANA MOCANU": "009011",
            "LAURA PLAZA DIAGO": "009017",
            "BEATRIZ VAZQUEZ JIMENEZ": "009018",
            "JOSE MARIA ALVAREZ OSUNA": "009039",
            "JACKY KESLASSY": "009040",
            "BEATRIZ MELENDEZ LEON": "009041",
            "MERCEDES LERENA LIQUIÑANO": "009042",
            "ISABEL RODRIGUEZ": "009044",
            "ISABEL ROMERO": "009045",
            "RAMON SANCHEZ": "009046",
            "BEBA SALCEDO": "009065"
        }
        
        try:
            # Verificar si hay registros en la tabla
            self.cursor.execute(f"SELECT COUNT(*) FROM {TABLA_REGISTROS}")
            total_registros = self.cursor.fetchone()[0]
            
            if total_registros == 0:
                messagebox.showinfo("Actualización", "No hay registros para actualizar.")
                return True
            
            # Verificar qué usuarios existen actualmente en la BD
            self.cursor.execute(f"SELECT DISTINCT user FROM {TABLA_REGISTROS} WHERE user IS NOT NULL AND user != ''")
            usuarios_existentes = [row[0] for row in self.cursor.fetchall()]
            
            # Usar transacción con context manager (más seguro)
            with self.conexion:
                # 1) Actualizar user -> id
                update_user_sql = f"UPDATE {TABLA_REGISTROS} SET user = ? WHERE user = ?"
                total_actualizados = 0
                
                for nombre_completo, user_id in empleados_mapping.items():
                    if nombre_completo in usuarios_existentes:
                        self.cursor.execute(update_user_sql, (user_id, nombre_completo))
                        filas_afectadas = self.cursor.rowcount
                        total_actualizados += filas_afectadas
                
                # 2) Limpiar la columna concepto en registros 'working'
                self.cursor.execute(f"SELECT COUNT(*) FROM {TABLA_REGISTROS} WHERE state = 'working'")
                registros_working = self.cursor.fetchone()[0]
                conceptos_limpiados = 0
                
                if registros_working > 0:
                    clear_concept_sql = f"UPDATE {TABLA_REGISTROS} SET concepto = '' WHERE state = 'working'"
                    self.cursor.execute(clear_concept_sql)
                    conceptos_limpiados = self.cursor.rowcount
            
            # Mensaje final de éxito
            mensaje = f"Actualización completada exitosamente:\n\n"
            mensaje += f"• {total_actualizados} registros de usuario actualizados\n"
            mensaje += f"• {conceptos_limpiados} conceptos limpiados"
            messagebox.showinfo("Actualización Exitosa", mensaje)
            return True
                
        except Exception as e:
            messagebox.showerror(
                "Error de Actualización",
                f"Hubo un problema al actualizar usuarios o limpiar conceptos:\n{str(e)}"
            )
            return False