import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

# Definición centralizada de las columnas y sus tipos, incluyendo 'observaciones'
COLUMNAS_DB: Dict[str, str] = {
    "tiempo": "TEXT",
    "empresa": "TEXT",
    "concepto": "TEXT",
    "fecha_creacion": "DATETIME",
    "fecha_imputacion": "DATETIME",
    "state": "TEXT",
    "user": "TEXT",
    "departamento": "TEXT",
    "observaciones": "TEXT"
}

TABLA_REGISTROS = "registros"

class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self.columnas: Dict[str, str] = COLUMNAS_DB.copy()
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

    def agregar_registro(self, tiempo: str, empresa: str, concepto: str, user: str, departamento: str, observaciones: str = "") -> int:
        """
        Agrega un nuevo registro a la base de datos, incluyendo el campo 'observaciones'.
        """
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M")
        query = f"""
            INSERT INTO {TABLA_REGISTROS} (tiempo, empresa, concepto, fecha_creacion, state, user, departamento, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (tiempo, empresa, concepto, fecha_creacion, "working", user, departamento, observaciones))
        self.conexion.commit()
        return str(self.cursor.lastrowid)

    def obtener_registro(self, registro_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro de la base de datos por su ID y devuelve un diccionario con columna: valor.
        Se incluye el campo 'observaciones'.
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

    def actualizar_registro(self, registro_id: int, nuevos_valores: Optional[Dict[str, Any]] = None, tiempo: Optional[str] = None) -> None:
        """
        Actualiza un registro en la base de datos con los nuevos valores o solo el tiempo.
        Se contempla el campo 'observaciones' si se incluye en nuevos_valores.
        """
        if tiempo is not None:
            query = f"UPDATE {TABLA_REGISTROS} SET tiempo = ? WHERE id = ?"
            self.cursor.execute(query, (tiempo, registro_id))
        elif nuevos_valores:
            columnas_actualizar = [col for col in nuevos_valores.keys() if col in self.columnas]
            set_clause = ", ".join(f"{col} = ?" for col in columnas_actualizar)
            valores = [nuevos_valores[col] for col in columnas_actualizar] + [registro_id]
            query = f"UPDATE {TABLA_REGISTROS} SET {set_clause} WHERE id = ?"
            self.cursor.execute(query, valores)
        else:
            raise ValueError("Debe proporcionar nuevos valores o un tiempo a actualizar.")
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












# import sqlite3
# from datetime import datetime
# from functions import COLUMNAS_DB


# class DatabaseManager:
#     def __init__(self, db_path):
#         # Definir columnas como variable de instancia
#         self.COLUMNAS = ["tiempo", "empresa", "concepto", "fecha_creacion",
#                          "fecha_imputacion", "state", "user", "departamento"]
        
#         # Conectar a SQLite
#         self.conexion = sqlite3.connect(db_path)
#         self.cursor = self.conexion.cursor()
#         self._crear_tabla()

#     def _crear_tabla(self):
#         """
#         Crea la tabla en SQLite si no existe.
#         """
#         self.cursor.execute("""
#             CREATE TABLE IF NOT EXISTS registros (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 tiempo TEXT,
#                 empresa TEXT,
#                 concepto TEXT,
#                 fecha_creacion DATETIME,
#                 fecha_imputacion DATETIME,
#                 state TEXT,
#                 user TEXT,
#                 departamento TEXT
#             )
#         """)
#         self.conexion.commit()


#     def obtener_registros(self, user):
#         """
#         Obtiene todos los registros de un usuario específico con estado 'working'.
#         """
#         self.cursor.execute("""
#             SELECT id, tiempo, empresa, concepto, fecha_creacion
#             FROM registros 
#             WHERE state = 'working' AND user = ?
#         """, (user,))
        
#         registros = self.cursor.fetchall()

#         # Convertir a lista de diccionarios
#         columnas = ["id", "tiempo", "empresa", "concepto", "fecha_creacion"]
#         return [dict(zip(columnas, row)) for row in registros]


#     def agregar_registro(self, tiempo, empresa, concepto, user, departamento):
#         """
#         Agrega un nuevo registro a la base de datos.
#         """
#         fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M")
#         self.cursor.execute("""
#             INSERT INTO registros (tiempo, empresa, concepto, fecha_creacion, state, user, departamento)
#             VALUES (?, ?, ?, ?, ?, ?, ?)
#         """, (tiempo, empresa, concepto, fecha_creacion, "working", user, departamento))
#         self.conexion.commit()
#         return self.cursor.lastrowid

#     def obtener_registro(self, registro_id):
#         """
#         Obtiene un registro de la base de datos por su ID y devuelve un diccionario con columna: valor.
#         """
#         self.cursor.execute("""
#             SELECT id, tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, state, user, departamento
#             FROM registros
#             WHERE id = ?
#         """, (registro_id,))
#         registro = self.cursor.fetchone()
#         if registro:
#             columnas = ["id", "tiempo", "empresa", "concepto", "fecha_creacion", "fecha_imputacion", "state", "user", "departamento"]
#             return dict(zip(columnas, registro))
#         return None


#     def actualizar_registro(self, registro_id, nuevos_valores=None, tiempo=None):
#         """
#         Actualiza un registro en la base de datos con los nuevos valores o solo el tiempo.
#         """
#         if tiempo is not None:
#             self.cursor.execute("""
#                 UPDATE registros
#                 SET tiempo = ?
#                 WHERE id = ?
#             """, (tiempo, registro_id))
#         elif nuevos_valores:
#             # columnas = ["tiempo", "empresa", "concepto", "fecha_creacion", 
#             #             "fecha_imputacion", "state", "user", "departamento"]
            
#             columnas = [col for col in nuevos_valores.keys() if col in self.COLUMNAS]
            
#             set_clause = ", ".join(f"{col} = ?" for col in columnas)
#             valores = [nuevos_valores[col] for col in columnas] + [registro_id]
            
#             self.cursor.execute(f"""
#                 UPDATE registros
#                 SET {set_clause}
#                 WHERE id = ?
#             """, valores)
#         else:
#             raise ValueError("Debe proporcionar nuevos valores o un tiempo a actualizar.")
        
#         self.conexion.commit()

#     def borrar_registro(self, registro_id):
#         """
#         Borra un registro de la base de datos.
#         """
#         self.cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
#         self.conexion.commit()

#     def cerrar_conexion(self):
#         """
#         Cierra la conexión con la base de datos.
#         """
#         self.conexion.close()