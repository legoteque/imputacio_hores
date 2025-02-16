from datetime import datetime
from tkinter import ttk

DB_PATH = r"data/treeview_data.db"
ICON = "assets/icono.ico"

CONFIG_FILE = "data/config.json"
DEFAULT_CONFIG = {"session": {"user": "", "pass": ""}}
EMPRESAS_CSV = "data/res_partner.csv"
NUEVAS_EMPRESAS_CSV = "data/new_partners.csv"
EMPLEADOS_CSV = "data/hr_employee.csv"


COLORES = {
    "blanco": "#ffffff",
    "negro": "#000000",
    "naranja": "#f39c12",
    "rojo": "#c0392b",
    "rojo2": "#dc3545",
    "rojo_hover": "#c82333",
    "rojo_oscuro": "#e74c3c",
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


def configure_styles():
    """Configura los estilos para ttk widgets."""
    style = ttk.Style()

    # Tema general
    style.theme_use("clam")

    # Estilo de Labels
    style.configure("TLabel", font=("Segoe UI", 10, "bold"), background=COLORES["rojo_oscuro"], foreground=COLORES["azul_claro"])
    style.configure("Timer.TLabel", font=("Segoe UI", 14, "bold"), background=COLORES["rojo_oscuro"], foreground=COLORES["blanco"])
    style.configure("PTimer.TLabel", font=("Segoe UI", 14, "bold"), background=COLORES["rojo_oscuro"], foreground=COLORES["gris_claro"])


    # Estilos de LabelFrame (para observaciones)
    style.configure("TLabelFrame", font=("Segoe UI", 11, "bold"), background="white", foreground="black", relief="solid", padding=5)

    # Estilos de LabelFrame dentro (label interior)
    style.configure("TLabelFrame.Label", font=("Segoe UI", 11, "bold"), foreground="black")

    # Estilo de Entries
    style.configure("TEntry", font=("Segoe UI", 11), padding=8, relief="flat", fieldbackground=COLORES["blanco"])
    style.map("TEntry", background=[("focus", COLORES["azul_claro"])])  # Azul claro en foco

    # Estilo de combobox
    style.configure("TCombobox", font=("Segoe UI", 11), padding=4, relief="flat")

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
    style.configure("Green.TButton", font=("Segoe UI", 14, "bold"), padding=5, foreground=COLORES["blanco"], background=COLORES["verde"])
    style.map("Green.TButton", background=[("active", COLORES["verde_hover"])])

    # Estilo rojo
    style.configure("Red.TButton", font=("Segoe UI", 14, "bold"), padding=5, foreground=COLORES["blanco"], background=COLORES["rojo"])
    style.map("Red.TButton", background=[("active", COLORES["rojo_oscuro"])])

    # 🔹 Estilo para el botón de pausa (gris claro)
    style.configure("Pause.TButton", font=("Segoe UI", 14, "bold"), padding=5, foreground=COLORES["blanco"], 
                    background=COLORES["gris_claro"], borderwidth=1)
    style.map("Pause.TButton", background=[("active", COLORES["gris_oscuro"])])  # Gris más oscuro al pasar el mouse

    # 🔹 Estilo para el botón de reanudar (verde claro)
    style.configure("Reanudar.TButton", font=("Segoe UI", 14, "bold"), padding=5, foreground=COLORES["blanco"],
                    background=COLORES["verde_claro"], borderwidth=1)
    style.map("Reanudar.TButton", background=[("active", COLORES["verde_oscuro"])])  # Verde más oscuro al pasar el mouse









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