from datetime import datetime

COLORES = {
    "blanco": "#ffffff",
    "negro": "#000000",
    "naranja": "#f39c12",
    "rojo": "#c0392b",
    "verde": "#2ecc71",
    "azul": "#3498db",
    "azul_claro": "#0000FF",
    "rojo_oscuro": "#e74c3c",
    "gris_claro": "#d3d3d3",
    "gris_oscuro": "#7d7d7d",
    "verde_claro": "#90EE90"
}

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
    Formatea una fecha del formato 'YYYY-MM-DD HH:MM:SS' a '1 de enero' o similar.
    """
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    return f"{fecha_dt.day} de {meses[fecha_dt.month - 1]}"

def return_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")