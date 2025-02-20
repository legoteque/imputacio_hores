import sqlite3
from datetime import datetime
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
            print("Error: register_dic es None en update_register()")
            return

        registro_id = nuevos_valores["id"]

        print(nuevos_valores)

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
            print(valores)
            self.cursor.execute(query, valores)
        else:
            raise ValueError("Debe proporcionar nuevos valores, un tiempo a actualizar o ambos.")
    
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
