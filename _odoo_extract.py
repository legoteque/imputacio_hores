import xmlrpc.client
import pandas as pd

# Configuración de conexión
url = "https://bi.etlfrenchdesk.es"
db = "etl_db"
username = "etalabardon@etl.es"
api_key = "3ed35d9a8633397ea1aef3749d0b692d17303e26"

# Columnas seleccionadas para el modelo res.partner
campos_res_partner = ["name", "vat", "is_company"]

# Columnas seleccionadas para el modelo hr.employee
campos_hr_employee = ["name", "department_id", "work_email"]

# Conexión a la API
def conectar_a_odoo():
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, api_key, {})
    if not uid:
        raise ValueError("Error: Credenciales incorrectas o usuario no autorizado.")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    print("Conexión exitosa a la API de Odoo.")
    return uid, models

# Función para extraer datos de un modelo
def extraer_datos(models, uid, model_name, fields):
    return models.execute_kw(
        db, uid, api_key,
        model_name, 'search_read',
        [[], fields]
    )

# Función para generar un CSV de res.partner
def generar_csv_res_partner(uid, models):
    print("Extrayendo datos del modelo res.partner...")
    datos = extraer_datos(models, uid, "res.partner", campos_res_partner)

    if datos:
        print("Datos extraídos exitosamente.")
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos)

        # Filtrar los registros donde is_company sea True y eliminar la columna is_company
        if 'is_company' in df.columns:
            df = df.loc[df['is_company'] == True]
            df = df.drop(columns=['is_company'])

        # Limpiar los nombres de empresa
        if 'name' in df.columns:
            df['name'] = df['name'].str.replace(r'\s+', ' ', regex=True).str.strip()  # Reducir espacios múltiples a uno
            df['name'] = df['name'].str.upper() #todos en mayusculas

        # Guardar en un archivo CSV
        archivo_csv = r"data/res_partner.csv"
        df.to_csv(archivo_csv, index=False)

        print(f"Datos del modelo res.partner guardados exitosamente en: {archivo_csv}")
    else:
        print("No se encontraron datos para el modelo res.partner.")

# Función para generar un CSV de hr.employee
def generar_csv_hr_employee(uid, models):
    print("Extrayendo datos del modelo hr.employee...")
    datos = extraer_datos(models, uid, "hr.employee", campos_hr_employee)

    if datos:
        print("Datos extraídos exitosamente.")
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos)

        # Convertir los nombres a mayúsculas
        if 'name' in df.columns:
            df['name'] = df['name'].str.upper()

        # Separar department_id en dos columnas: department_id y department_name
        if 'department_id' in df.columns:
            df[['department_id', 'department_name']] = df['department_id'].apply(
                lambda x: pd.Series([x[0], x[1].replace("'", "")]) if isinstance(x, list) and len(x) == 2 else pd.Series([None, None])
            )
            # Convertir department_id a entero
            df['department_id'] = df['department_id'].astype('Int64')

        # Guardar en un archivo CSV
        archivo_csv = r"data/hr_employee.csv"
        df.to_csv(archivo_csv, index=False)

        print(f"Datos del modelo hr.employee guardados exitosamente en: {archivo_csv}")
    else:
        print("No se encontraron datos para el modelo hr.employee.")

# Ejecutar el script
if __name__ == "__main__":
    try:
        uid, models = conectar_a_odoo()
        generar_csv_res_partner(uid, models)
        generar_csv_hr_employee(uid, models)
    except Exception as e:
        print("Error al generar los archivos CSV:", e)
