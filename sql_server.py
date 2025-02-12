import pyodbc

# Configuración de conexión
SQL_SERVER = '89.117.61.152'
SQL_DATABASE = 'ETL_DATA'
SQL_USERNAME = 'airflow'
SQL_PASSWORD = 'sqlHPml350+'

def conectar_sql():
    """ Establece la conexión con SQL Server y devuelve el cursor y la conexión """
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}')
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"❌ Error conectando a SQL Server: {e}")
        return None, None

def insertar_registros(datos):
    """
    Inserta registros en la tabla 'imputacion_tiempos' en SQL Server.
    `datos` debe ser una lista de tuplas con los valores correspondientes.
    """
    conn, cursor = conectar_sql()
    if not conn:
        return False  # Falla la conexión

    try:
        cursor.executemany("""
            INSERT INTO imputacion_tiempos (tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, state, [user], departamento, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, datos)
        conn.commit()
        print(f"✅ {len(datos)} registros insertados en SQL Server.")
        return True  # Inserción exitosa
    except Exception as e:
        print(f"❌ Error insertando en SQL Server: {e}")
        return False
    finally:
        conn.close()



# Obtener los datos de los registros imputados para SQL Server
datos_a_subir = []
for item_id in items_a_imputar:
    registro = self.db_manager.obtener_registro(item_id)
    if registro:
        datos_a_subir.append((
            registro["tiempo"], registro["empresa"], registro["concepto"],
            registro["fecha_creacion"], registro["fecha_imputacion"], 
            registro["state"], registro["user"], registro["departamento"], ''
        ))

if not datos_a_subir:
    print("⚠️ No se encontraron datos para subir a SQL Server.")
    return

# Paso 2: Subir datos a SQL Server
if insertar_registros(datos_a_subir):
    # Paso 3: Confirmar en SQLite que los registros fueron imputados correctamente
    for item_id in items_a_imputar:
        db_manager.actualizar_registro(item_id, nuevos_valores={"state": "imputado"})

    print(f"✅ Registros {items_a_imputar} imputados correctamente en SQL Server y actualizados en SQLite.")
else:
    print(f"❌ Error en la conexión a SQL Server. Los registros quedan en estado 'imputando'.")