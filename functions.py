from datetime import datetime
from tkinter import ttk
import os, gdown


# Obtener el directorio del usuario en Windows
USER_PATH = os.path.expanduser("~")  # Esto devuelve algo como C:\Users\TuUsuario

FILES_PATH = os.path.join(USER_PATH, ".imputaciones")  # Crea la ruta completa

DB_PATH = os.path.join(FILES_PATH, "register.db")


ICON_URL = "https://drive.google.com/file/d/1GMNgEZ4f1rBfd2swr786wYF-6buv4o6H/view?usp=sharing"

ICON = os.path.join(FILES_PATH, "icono.ico")

CONFIG_FILE = os.path.join(FILES_PATH, "config.json")
DEFAULT_CONFIG = {"session": {"user": "", "pass": ""}}
# EMPRESAS_CSV = "data/res_partner.csv"
# NUEVAS_EMPRESAS_CSV = "data/new_partners.csv"
# EMPLEADOS_CSV = "data/hr_employee.csv"

# Configuración de conexión
# Configuración de conexión
SQLSERVER_CONFIG = {"server": "srv-suasor",
                    "database": "INTERNA",
                    "username": "conexionsql",
                    "password": "conexionSQL2025"}


COLORES = {
    "blanco": "#ffffff",
    "negro": "#000000",
    "naranja": "#f39c12",
    "rojo": "#c0392b",
    "rojo2": "#dc3545",
    "rojo_hover": "#c82333",
    "rojo_oscuro": "#e74c3c",
    "granate": "#8B0000",
    "verde_lcd": "#90EE90",
    "verde_claro": "#90EE90",
    "verde": "#2ecc71",
    "verde2": "#28a745",
    "verde_oscuro": "#008F4C",
    "verde_hover": "#218838",
    "azul": "#3498db",
    "azul_claro": "#e3f2fd",
    "azul_oscuro": "#0056b3",
    "gris_claro": "#d3d3d3",
    "gris_oscuro": "#A0A0A0"  
}


COLUMNAS_TREE = (
        "checkbox",
        "tiempo",
        "empresa",
        "concepto",
        "fecha_creacion",
        "time",
        "date",
    )

COLUMNAS_DB = (
        "id",
        "tiempo",
        "empresa",
        "concepto",
        "fecha_creacion",
        "fecha_imputacion",
        "state",
        "user",
        "departamento",
    )


def verificar_o_crear_carpeta_archivos():
    """Verifica si la carpeta .imputaciones existe en el path del usuario de Windows. Si no existe, la crea."""
    
    # Verificar si la carpeta existe
    if not os.path.exists(FILES_PATH):
        os.makedirs(FILES_PATH)  # Crear la carpeta si no existe

    #si no tenemos el icono descargado, lo descargamos
    if not os.path.exists(ICON):
        # Extraer el ID del archivo de la URL
        file_id = ICON_URL.split("/d/")[1].split("/")[0]
        # Construir la URL directa de descarga
        download_url = f"https://drive.google.com/uc?id={file_id}"
        # Nombre del archivo de salida
        output_file = os.path.join(FILES_PATH, "icono.ico")
        # Descargar el archivo
        gdown.download(download_url, output_file, quiet=False)


def procesar_nombre(name):
    """Procesa un string eliminando 'de' y 'los', y eliminando las dos últimas palabras si quedan tres o más.
    Si tras eliminar 'de' y 'los' quedan menos de tres palabras, devuelve el nombre original."""
    # Eliminar palabras que contienen "de" o "los" (ignorando mayúsculas/minúsculas)
    palabras = [word for word in name.split() if word.lower() not in ["de", "los"]]
    
    # Si quedan menos de tres palabras después del filtro, devolver el nombre original
    if len(palabras) < 3:
        return name
    
    # Si quedan 3 o más palabras, quitar las dos últimas
    palabras = palabras[:-2]
    
    # Unir el resultado en una cadena
    return " ".join(palabras)


def seconds_to_string(time, include_seconds=True):
    time = int(time)
    hours = time // 3600
    minutes = (time % 3600) // 60
    seconds = time % 60
    
    if include_seconds:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    if hours > 0:
        if hours == 1:
            return f"1 hora {minutes} min."
        return f"{hours} horas {minutes} min."
    return f"{minutes} min."


@staticmethod
def formatear_fecha(fecha):
    """
    Formatea una fecha del formato 'YYYY-MM-DD HH:MM' a '1 de enero' o similar.
    """
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M")
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    return f"{fecha_dt.day} de {meses[fecha_dt.month - 1]}"

def return_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def configure_styles():
    """Configura los estilos para ttk widgets."""
    style = ttk.Style()

    # Tema general
    style.theme_use("clam")

    # Estilo de Labels
    style.configure("TLabel", font=("Segoe UI", 10, "bold"), background=COLORES["rojo_oscuro"], foreground=COLORES["azul_claro"])
    # Estilos personalizados
    style.configure("Timer.TLabel", font=("OCR A Extended", 22, "bold"), background=COLORES["negro"], foreground=COLORES["verde_lcd"],
                    padding=3, relief="solid", borderwidth=5, anchor="center")
    style.configure("PTimer.TLabel", font=("OCR A Extended", 22, "bold"), background=COLORES["negro"], foreground=COLORES["gris_claro"],
                    padding=3, relief="solid", borderwidth=5, anchor="center")
    
    style.configure("Main.TLabel", font=("Segoe UI", 11, "bold"), background=COLORES["granate"], foreground=COLORES["blanco"],
                    padding=(3), relief="solid", borderwidth=5, anchor="center")

    # Estilos de LabelFrame (para descripcion)
    style.configure("TLabelFrame", font=("Segoe UI", 11, "bold"), background="white", foreground="black", relief="solid", padding=5)

    # Estilos de LabelFrame dentro (label interior)
    style.configure("TLabelFrame.Label", font=("Segoe UI", 11, "bold"), foreground="black")

    # Estilo de Entries
    style.configure("TEntry", font=("Segoe UI", 11), padding=(3), relief="flat", fieldbackground=COLORES["blanco"])
    style.map("TEntry", background=[("focus", COLORES["azul_claro"])])  # Azul claro en foco

    # Estilo de combobox
    style.configure("TCombobox", font=("Segoe UI", 11), padding=(3), relief="flat")

    # Estilo de Botones (flat con hover)
    style.configure("Flat.TButton", font=("Segoe UI", 11, "bold"), padding=10, foreground="white", background="#007bff", relief="flat")
    style.map("Flat.TButton", background=[("active", COLORES["azul_oscuro"])])  # Azul más oscuro al pasar el ratón

    #Button
    # style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=5, relief="flat", 
    #                 background=COLORES["rojo_oscuro"], foreground=COLORES["blanco"])
    # style.map("TButton", background=[("active", COLORES["rojo"])] )

    #Logout button
    style.configure("Logout.TButton", font=("Segoe UI", 8, "bold"), padding=5, foreground=COLORES["blanco"], background=COLORES["rojo"])
    style.map("Logout.TButton", background=[("active", COLORES["rojo_oscuro"])])

    # Estilo verde
    style.configure("Play.TButton", font=("Segoe UI", 14, "bold"), foreground=COLORES["blanco"], background=COLORES["verde"], 
                    padding=5, relief="solid", borderwidth=5)
    style.map("Play.TButton", background=[("active", COLORES["verde_hover"])])

    # Estilo rojo
    style.configure("Stop.TButton", font=("Segoe UI", 14, "bold"), foreground=COLORES["blanco"], background=COLORES["rojo"], 
                    padding=5, relief="solid", borderwidth=5)
    style.map("Stop.TButton", background=[("active", COLORES["rojo_oscuro"])])

    # 🔹 Estilo para el botón de pausa (gris claro)
    style.configure("Pause.TButton", font=("Segoe UI", 14, "bold"), foreground=COLORES["blanco"], background=COLORES["gris_claro"], 
                    padding=5, relief="solid", borderwidth=5)
    style.map("Pause.TButton", background=[("active", COLORES["gris_oscuro"])])  # Gris más oscuro al pasar el mouse

    # 🔹 Estilo para el botón de reanudar (verde claro)
    style.configure("Reanudar.TButton", font=("Segoe UI", 14, "bold"), foreground=COLORES["blanco"], background=COLORES["verde_claro"], 
                    padding=5, relief="solid", borderwidth=5)
    style.map("Reanudar.TButton", background=[("active", COLORES["verde_oscuro"])])  # Verde más oscuro al pasar el mouse