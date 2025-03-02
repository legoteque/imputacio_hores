import sqlite3
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Definición centralizada de las columnas y sus tipos, incluyendo 'descripcion'
COLUMNAS_DB: Dict[str, str] = {
    "tiempo": "TEXT",
    "empresa": "TEXT",
    "concepto": "TEXT",
    "fecha_creacion": "DATETIME",
    "fecha_imputacion": "DATETIME",
    "state": "TEXT",
    "user": "TEXT",
    "departamento": "TEXT",
    "descripcion": "TEXT",
    "vinculada": "INTEGER",
    "cif": "TEXT"
}

TABLA_REGISTROS = "registros"

class DatabaseManager:
    def __init__(self, app, db_path: str) -> None:
        self.app = app
        self.db_path = db_path
        self.columnas: Dict[str, str] = COLUMNAS_DB.copy()
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        self._crear_tabla()
        self.sincronizar_tabla("empleados")
        self.sincronizar_tabla("empresas")

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


    def sincronizar_tabla(self, tabla_origen, tabla_destino=None):
        """Sincroniza todos los datos de una tabla de SQL Server a SQLite."""
        if tabla_destino is None:
            tabla_destino = tabla_origen

        # 1️⃣ Verificar conexión a SQL Server
        if not self.app.sql_server_manager.comprobar_conexion():
            return

        try:
            # 2️⃣ Iniciar transacción en SQLite
            self.cursor.execute("BEGIN TRANSACTION")
            
            # 3️⃣ Eliminar tabla en SQLite si existe
            self.cursor.execute(f'DROP TABLE IF EXISTS "{tabla_destino}"')

            # 4️⃣ Obtener estructura de la tabla en SQL Server
            columnas = self.app.sql_server_manager.obtener_estructura_tabla(tabla_origen)
            columnas_nombres = [columna[0] for columna in columnas]

            # 5️⃣ Mapear tipos de datos de SQL Server a SQLite
            tipo_mapeo = {
                "int": "INTEGER",
                "bigint": "INTEGER",
                "smallint": "INTEGER",
                "tinyint": "INTEGER",
                "bit": "INTEGER",
                "nvarchar": "TEXT",
                "varchar": "TEXT",
                "text": "TEXT",
                "datetime": "TEXT",
                "date": "TEXT",
                "float": "REAL",
                "decimal": "REAL",
                "numeric": "REAL",
                "money": "REAL",
                "uniqueidentifier": "TEXT"
            }

            columnas_definicion = [f'"{col}" {tipo_mapeo.get(tipo.lower(), "TEXT")}' for col, tipo in columnas]
            sql_crear_tabla = f'CREATE TABLE "{tabla_destino}" ({", ".join(columnas_definicion)})'
            self.cursor.execute(sql_crear_tabla)

            # 6️⃣ Obtener datos desde SQL Server
            datos = self.app.sql_server_manager.obtener_datos_tabla(tabla_origen)

            # 7️⃣ Función para convertir valores problemáticos
            def convertir_valor(valor):
                if isinstance(valor, Decimal):
                    return float(valor)
                elif isinstance(valor, datetime):
                    return valor.strftime("%Y-%m-%d %H:%M:%S")  # Formato estándar ISO
                elif valor is None:
                    return None  # Mantener NULL en SQLite
                return valor

            # Convertir datos de SQL Server a formatos adecuados para SQLite
            datos_convertidos = [tuple(map(convertir_valor, fila)) for fila in datos]

            # 8️⃣ Insertar datos en SQLite
            if datos_convertidos:
                placeholders = ", ".join(["?"] * len(columnas_nombres))
                columnas_escapadas = [f'"{col}"' for col in columnas_nombres]
                sql_insert = f'INSERT INTO "{tabla_destino}" ({", ".join(columnas_escapadas)}) VALUES ({placeholders})'
                self.cursor.executemany(sql_insert, datos_convertidos)
                self.conexion.commit()
                #print(f"✅ Tabla '{tabla_destino}' importada correctamente con {len(datos_convertidos)} registros.")


        except Exception as e:
            self.conexion.rollback()
            #print(f"❌ Error durante la sincronización de la tabla {tabla_origen}: {e}")

    def load_empleados_sqlite(self):
        """Carga los empleados desde SQLite en un DataFrame de pandas."""
        query = """
            SELECT id, name, department_id, work_email, department_name 
            FROM empleados
            WHERE department_name IS NOT NULL AND department_name != 'Administration'
        """
        
        try:
            self.cursor.execute(query)
            empleados_data = self.cursor.fetchall()
            empleados_df = pd.DataFrame(empleados_data, columns=[col[0] for col in self.cursor.description])
            empleados_l = empleados_df['name'].tolist()  # Lista de nombres
            return empleados_l, empleados_df
        except Exception as e:
            #print(f"Error al cargar empleados desde SQLite: {e}")
            return [], pd.DataFrame()

    def load_empresas_sqlite(self):
        """Carga las empresas desde SQLite en un DataFrame de pandas."""
        query = "SELECT id, name, vat FROM empresas"
        
        try:
            self.cursor.execute(query)
            empresas_data = self.cursor.fetchall()
            empresas_df = pd.DataFrame(empresas_data, columns=[col[0] for col in self.cursor.description])
            return empresas_df
        except Exception as e:
            #print(f"Error al cargar empresas desde SQLite: {e}")
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
        
        :param db_path: Ruta de la base de datos SQLite.
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
            #print("Error: register_dic es None en update_register()")
            return

        registro_id = nuevos_valores["id"]

        #print(nuevos_valores)

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
            #print(valores)
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
        Obtiene el CIF de 'empresa_real' desde 'self.empresas_dic' y establece 'vinculada' en 1.

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

        #print(f"Se han actualizado los registros de '{empresa_anterior}' a '{empresa_real}' con CIF '{cif_real}' y vinculada '1'.")


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





