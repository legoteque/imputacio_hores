from datetime import datetime
import tkinter as tk
from tkinter import ttk
import os, gdown


# Obtener el directorio del usuario en Windows
USER_PATH = os.path.expanduser("~")  # Esto devuelve algo como C:\Users\TuUsuario

FILES_PATH = os.path.join(USER_PATH, ".imputaciones")  # Crea la ruta completa

DB_PATH = os.path.join(FILES_PATH, "register.db")


ICON_URL = "https://drive.google.com/file/d/1GMNgEZ4f1rBfd2swr786wYF-6buv4o6H/view?usp=sharing"

ICON = os.path.join(FILES_PATH, "icono.ico")

CONFIG_FILE = os.path.join(FILES_PATH, "config.json")
DEFAULT_CONFIG = {"session": {"id": ""}, "version": "1.1"}

# Configuración de conexión
SQLSERVER_CONFIG = {
    "servers": [
        "192.168.55.7",
        "srv-suasor",      # Servidor primario (dominio)
        "192.168.55.7"     # Servidor de fallback (IP)
    ],
    "port": "1433",
    "database": "INTERNA",
    "username": "conexionsql",
    "password": "conexionSQL2025",
    "clientes_tbl": "DimClientes",
    "empleados_tbl": "DimEmpleados",
    "imputaciones_tbl": "Fact_Imputado",
    "conceptos_tbl": "DimConceptos",
    "connection_timeout": 8,  # Timeout más corto para fallback rápido
    "trust_certificate": "yes",
    "encrypt": "no"
}

SQLSERVER_CONFIG = {
    "servers": [
        "192.168.55.7",  # ✅ Servidor primario (IP) - probado primero
        "srv-suasor"     # ✅ Servidor de fallback (dominio) - solo si el primero falla
    ],
    "port": "1433",
    "database": "INTERNA",
    "username": "conexionsql",
    "password": "conexionSQL2025",
    "clientes_tbl": "DimClientes",
    "empleados_tbl": "DimEmpleados",
    "imputaciones_tbl": "Fact_Imputado",
    "conceptos_tbl": "DimConceptos",
    "connection_timeout": 3,      # ✅ REDUCIDO: 3 segundos vs 8 anteriores
    "login_timeout": 3,           # ✅ NUEVO: timeout específico de login
    "network_timeout": 2,         # ✅ NUEVO: timeout de verificación de red
    "trust_certificate": "yes",
    "encrypt": "no"
}

EMPLEADOS_COLS = {
    "id": "INTEGER PRIMARY KEY",
    "nombre": "TEXT NOT NULL",
    "apellido_1": "TEXT",
    "apellido_2": "TEXT",
    "department_name": "TEXT",
    "activo": "INTEGER DEFAULT 1"
}

CLIENTES_COLS = {
    "vat": "TEXT PRIMARY KEY",
    "name": "TEXT NOT NULL", 
    "origen": "TEXT",
    "baja": "INTEGER DEFAULT 0"
}

CONCEPTOS_COLS = {
    "Cod_ concepto": "TEXT",
    "Descripcion": "TEXT", 
    "Cod_ modulo": "TEXT",
    "num_facturas": "INTEGER",
    "ultima_fecha": "TEXT",
    "periodo": "TEXT"
}

REGISTRO_COLS = {
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

# IMPUTADO_COLS = [id, tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, 
#                  usuario, departamento, descripcion, cif]

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
    "fecha_creacion",
    "empresa",
    "concepto", 
    "tiempo",
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
    
    try:
        style = ttk.Style()
        
        # Configurar tema base
        if "clam" in style.theme_names():
            style.theme_use("clam")
        else:
            style.theme_use("default")

        # ===== LABELS =====
        # Label básico
        style.configure("TLabel", font=("Segoe UI", 10, "bold"), 
                       background=COLORES["rojo_oscuro"], 
                       foreground=COLORES["azul_claro"])
        
        # Label principal del usuario
        style.configure("Main.TLabel", font=("Segoe UI", 11, "bold"), 
                       background=COLORES["granate"], 
                       foreground=COLORES["blanco"], 
                       padding=(3, 3, 3, 0), relief="solid", borderwidth=5, anchor="w")
        
        # Labels del temporizador
        style.configure("Timer.TLabel", font=("OCR A Extended", 22, "bold"), 
                       background=COLORES["negro"], 
                       foreground=COLORES["verde_lcd"],
                       padding=3, relief="solid", borderwidth=5, anchor="center")
        
        style.configure("PTimer.TLabel", font=("OCR A Extended", 22, "bold"), 
                       background=COLORES["negro"], 
                       foreground=COLORES["gris_claro"],
                       padding=3, relief="solid", borderwidth=5, anchor="center")

        # ===== CAMPOS DE ENTRADA =====
        style.configure("TEntry", font=("Segoe UI", 11), padding=(3), relief="flat", 
                       fieldbackground=COLORES["blanco"])
        style.map("TEntry", background=[("focus", COLORES["azul_claro"])])
        
        style.configure("TCombobox", font=("Segoe UI", 11), padding=(3), relief="flat")

        # ===== FRAMES =====
        style.configure("TLabelFrame", font=("Segoe UI", 11, "bold"), 
                       background="white", foreground="black", relief="solid", padding=5)
        
        style.configure("TLabelFrame.Label", font=("Segoe UI", 11, "bold"), foreground="black")

        # ===== BOTONES DE CONTROL DE TIEMPO =====
        style.configure("Play.TButton", font=("Segoe UI", 14, "bold"), 
                       foreground=COLORES["blanco"], background=COLORES["verde"], 
                       padding=5, relief="solid", borderwidth=5)
        style.map("Play.TButton", background=[("active", COLORES["verde_hover"])])

        style.configure("Stop.TButton", font=("Segoe UI", 14, "bold"), 
                       foreground=COLORES["blanco"], background=COLORES["rojo"], 
                       padding=5, relief="solid", borderwidth=5)
        style.map("Stop.TButton", background=[("active", COLORES["rojo_oscuro"])])

        style.configure("Pause.TButton", font=("Segoe UI", 14, "bold"), 
                       foreground=COLORES["blanco"], background=COLORES["gris_claro"], 
                       padding=5, relief="solid", borderwidth=5)
        style.map("Pause.TButton", background=[("active", COLORES["gris_oscuro"])])

        style.configure("Reanudar.TButton", font=("Segoe UI", 14, "bold"), 
                       foreground=COLORES["blanco"], background=COLORES["verde_claro"], 
                       padding=5, relief="solid", borderwidth=5)
        style.map("Reanudar.TButton", background=[("active", COLORES["verde_oscuro"])])

        # ===== BOTONES DEL HEADER =====
        style.configure("Logout.TButton", font=("Segoe UI", 9, "bold"), padding=5, 
                       foreground=COLORES["blanco"], background=COLORES["rojo"])
        style.map("Logout.TButton", background=[("active", COLORES["rojo_oscuro"])])

        style.configure("Insert.TButton", 
                       font=("Segoe UI", 9, "bold"), 
                       padding=(8, 4), 
                       foreground="white", 
                       background="#27ae60",  # Verde profesional
                       relief="flat", 
                       borderwidth=0)
        style.map("Insert.TButton", 
                  background=[("active", "#229954"),  # Verde más oscuro al hover
                             ("pressed", "#1e8449")])  # Verde aún más oscuro al presionar
        
        style.configure("Sync.TButton", 
                       font=("Segoe UI", 9, "bold"), 
                       padding=(8, 4), 
                       foreground="white", 
                       background="#3498db",  # Azul profesional
                       relief="flat", 
                       borderwidth=0)
        style.map("Sync.TButton", 
                  background=[("active", "#2980b9"),  # Azul más oscuro al hover
                             ("pressed", "#1f618d")])  # Azul aún más oscuro al presionar

        # ===== BOTONES GENERALES =====
        style.configure("Flat.TButton", font=("Segoe UI", 11, "bold"), padding=10, 
                       foreground="white", background="#007bff", relief="flat")
        style.map("Flat.TButton", background=[("active", COLORES["azul_oscuro"])])
        
    except Exception as e:
        print(f"❌ ERROR en configure_styles(): {e}")
        import traceback
        traceback.print_exc()



class CustomMessageBox:
    """Sistema de mensajes personalizado que aparece centrado sobre la ventana padre."""
    
    @staticmethod
    def showerror(title, message, parent=None):
        """Muestra mensaje de error personalizado."""
        return CustomMessageBox._show_message(title, message, "error", parent)
    
    @staticmethod
    def showinfo(title, message, parent=None):
        """Muestra mensaje de información personalizado."""
        return CustomMessageBox._show_message(title, message, "info", parent)
    
    @staticmethod
    def showwarning(title, message, parent=None):
        """Muestra mensaje de advertencia personalizado."""
        return CustomMessageBox._show_message(title, message, "warning", parent)
    
    @staticmethod
    def askyesno(title, message, parent=None):
        """Muestra mensaje de confirmación Sí/No."""
        return CustomMessageBox._show_message(title, message, "yesno", parent)
    
    @staticmethod
    def _show_message(title, message, msg_type, parent):
        """Método interno para mostrar mensajes."""
        
        # ✅ SIEMPRE USAR LA VENTANA PRINCIPAL COMO REFERENCIA
        # Buscar la ventana root principal
        if parent:
            # Si parent es una ventana hija, buscar la root principal
            root_window = parent
            while hasattr(root_window, 'master') and root_window.master:
                root_window = root_window.master
        else:
            root_window = tk._default_root
        
        # Crear ventana de mensaje
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        
        # ✅ CONFIGURACIÓN MODAL ABSOLUTA
        dialog.transient(root_window)  # Siempre relativo a root
        dialog.grab_set()              # Bloquear toda interacción
        dialog.attributes("-topmost", True)  # Siempre en primer plano
        dialog.focus_force()           # Forzar foco
        
        # Variable para almacenar la respuesta
        result = None
        
        # ✅ FRAME PRINCIPAL CON PADDING COMPACTO
        main_frame = tk.Frame(dialog, bg="white", padx=15, pady=12)
        main_frame.pack(fill="both", expand=True)
        
        # Icono y configuración según el tipo
        icon_colors = {
            "error": {"bg": "#e74c3c", "fg": "white", "icon": "✖"},
            "info": {"bg": "#3498db", "fg": "white", "icon": "ℹ"},
            "warning": {"bg": "#f39c12", "fg": "white", "icon": "⚠"},
            "yesno": {"bg": "#9b59b6", "fg": "white", "icon": "?"}
        }
        
        colors = icon_colors.get(msg_type, icon_colors["info"])
        
        # ✅ FRAME DEL ENCABEZADO
        header_frame = tk.Frame(main_frame, bg=colors["bg"], relief="flat", bd=0)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # ✅ ICONO Y TÍTULO
        icon_label = tk.Label(header_frame, text=colors["icon"], 
                             bg=colors["bg"], fg=colors["fg"], 
                             font=("Arial", 14, "bold"), pady=6)
        icon_label.pack(side="left", padx=8)
        
        title_label = tk.Label(header_frame, text=title, 
                              bg=colors["bg"], fg=colors["fg"], 
                              font=("Arial", 11, "bold"), pady=6)
        title_label.pack(side="left", expand=True)
        
        # ✅ MENSAJE CON DIMENSIONES DINÁMICAS
        # Calcular dimensiones según el contenido del mensaje
        message_lines = message.count('\n') + 1
        message_length = len(message)
        
        # Determinar ancho base según longitud del mensaje
        if message_length <= 50:
            base_width = 280
        elif message_length <= 100:
            base_width = 350
        elif message_length <= 200:
            base_width = 420
        else:
            base_width = 500
        
        # Ajustar altura según número de líneas
        if message_lines > 3:
            # Para mensajes muy largos, permitir más altura
            base_width = min(base_width, 450)  # Limitar ancho máximo
        
        message_label = tk.Label(main_frame, text=message, 
                                bg="white", fg="#34495e", 
                                font=("Arial", 9), 
                                wraplength=base_width-40, justify="center")
        message_label.pack(pady=(0, 12))
        
        # ✅ FRAME DE BOTONES
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(fill="x")
        
        def close_dialog(response=None):
            nonlocal result
            result = response
            dialog.attributes("-topmost", False)  # Quitar topmost antes de cerrar
            dialog.destroy()
        
        # ✅ BOTONES
        if msg_type == "yesno":
            # Botón Sí
            yes_button = tk.Button(button_frame, text="Sí", 
                                  command=lambda: close_dialog(True),
                                  bg="#27ae60", fg="white", 
                                  font=("Arial", 9, "bold"),
                                  width=8, height=1, relief="flat",
                                  cursor="hand2")
            yes_button.pack(side="left", padx=(0, 8))
            
            # Botón No
            no_button = tk.Button(button_frame, text="No", 
                                 command=lambda: close_dialog(False),
                                 bg="#e74c3c", fg="white", 
                                 font=("Arial", 9, "bold"),
                                 width=8, height=1, relief="flat",
                                 cursor="hand2")
            no_button.pack(side="right", padx=(8, 0))
            
            # Focus en botón Sí por defecto
            yes_button.focus_set()
            
            # Manejar Enter y Escape
            dialog.bind('<Return>', lambda e: close_dialog(True))
            dialog.bind('<Escape>', lambda e: close_dialog(False))
            
        else:
            # ✅ BOTÓN ACEPTAR
            ok_button = tk.Button(button_frame, text="Aceptar", 
                                 command=lambda: close_dialog(True),
                                 bg=colors["bg"], fg=colors["fg"], 
                                 font=("Arial", 9, "bold"),
                                 width=12, height=1, relief="flat",
                                 cursor="hand2")
            ok_button.pack(expand=True)
            
            # Focus en botón Aceptar
            ok_button.focus_set()
            
            # Manejar Enter y Escape
            dialog.bind('<Return>', lambda e: close_dialog(True))
            dialog.bind('<Escape>', lambda e: close_dialog(True))
        
        # ✅ PREVENIR CIERRE ACCIDENTAL
        dialog.protocol("WM_DELETE_WINDOW", lambda: close_dialog(False if msg_type == "yesno" else True))
        
        # ✅ AJUSTAR TAMAÑO DESPUÉS DE CREAR TODO EL CONTENIDO
        dialog.update_idletasks()  # Permitir que Tkinter calcule tamaños
        
        # Obtener el tamaño real necesario
        req_width = dialog.winfo_reqwidth()
        req_height = dialog.winfo_reqheight()
        
        # Aplicar límites mínimos y máximos
        min_width, min_height = 320, 160
        max_width, max_height = 600, 400
        
        final_width = max(min_width, min(req_width, max_width))
        final_height = max(min_height, min(req_height, max_height))
        
        # ✅ CENTRAR CON LAS DIMENSIONES FINALES
        root_window.update_idletasks()
        root_x = root_window.winfo_x()
        root_y = root_window.winfo_y()
        root_width = root_window.winfo_width()
        root_height = root_window.winfo_height()
        
        pos_x = root_x + (root_width - final_width) // 2
        pos_y = root_y + (root_height - final_height) // 2
        
        dialog.geometry(f"{final_width}x{final_height}+{pos_x}+{pos_y}")
        
        # ✅ ASEGURAR QUE MANTIENE EL FOCO
        def maintain_focus():
            if dialog.winfo_exists():
                dialog.lift()
                dialog.focus_force()
                dialog.after(100, maintain_focus)
        
        maintain_focus()
        
        # Mostrar ventana y esperar
        dialog.wait_window()
        
        return result


class ToolTip:
    """Tooltip como frame hijo de la ventana principal."""
    
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_frame = None
        self.timer_id = None
        
        # Obtener la ventana root principal
        self.root = widget.winfo_toplevel()
        
        # Vincular eventos
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        """Al entrar al widget, programar mostrar tooltip."""
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
        self.timer_id = self.widget.after(500, self.show_tooltip)
    
    def on_leave(self, event):
        """Al salir del widget, ocultar tooltip."""
        self.hide_tooltip()
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
    
    def show_tooltip(self):
        """Mostrar tooltip como frame dentro de la ventana principal."""
        if self.tooltip_frame:
            return
        
        try:
            # ✅ CREAR FRAME TOOLTIP DENTRO DE LA VENTANA PRINCIPAL
            self.tooltip_frame = tk.Frame(
                self.root,
                bg="#2d2d2d",
                relief="solid",
                bd=1
            )
            
            label = tk.Label(
                self.tooltip_frame,
                text=self.text,
                bg="#2d2d2d",
                fg="white",
                font=("Segoe UI", 9),
                padx=8,
                pady=4,
                justify="left"
            )
            label.pack()
            
            # ✅ CALCULAR POSICIÓN CORRECTA SUMANDO TODAS LAS POSICIONES PADRE
            total_x = 0
            total_y = 0
            
            # Empezar desde el widget y subir por la jerarquía
            current_widget = self.widget
            
            while current_widget and current_widget != self.root:
                # Sumar la posición de este widget
                total_x += current_widget.winfo_x()
                total_y += current_widget.winfo_y()
                
                # Subir al padre
                current_widget = current_widget.master
                
                # Debug: mostrar cada paso
                if current_widget != self.root:
                    print(f"   Sumando padre: {current_widget.__class__.__name__} en ({current_widget.winfo_x()}, {current_widget.winfo_y()}) -> Total: ({total_x}, {total_y})")
            
            # ✅ POSICIÓN FINAL (debajo del widget)
            widget_height = self.widget.winfo_height()
            final_x = total_x
            final_y = total_y + widget_height + 8  # 8px de separación
            
            # ✅ OBTENER DIMENSIONES DE LA VENTANA PARA AJUSTES
            root_width = self.root.winfo_width()
            root_height = self.root.winfo_height()
            
            # ✅ AJUSTAR SI SE SALE DE LA VENTANA
            self.tooltip_frame.update_idletasks()
            tooltip_width = self.tooltip_frame.winfo_reqwidth()
            tooltip_height = self.tooltip_frame.winfo_reqheight()
            
            # Ajustar horizontalmente
            if final_x + tooltip_width > root_width - 10:
                final_x = root_width - tooltip_width - 10
            
            if final_x < 10:
                final_x = 10
            
            # Ajustar verticalmente
            if final_y + tooltip_height > root_height - 10:
                # Mostrar arriba del widget en lugar de abajo
                final_y = total_y - tooltip_height - 8
                
            if final_y < 10:
                final_y = 10
            
            # ✅ COLOCAR EL TOOLTIP
            self.tooltip_frame.place(x=final_x, y=final_y)
            
            print(f"🎯 Widget: {self.widget.winfo_class()} -> Tooltip en: ({final_x}, {final_y}) [Calculado desde ({total_x}, {total_y}) + altura {widget_height}]")
            
        except Exception as e:
            print(f"❌ Error en tooltip frame: {e}")
            import traceback
            traceback.print_exc()
            self.hide_tooltip()
    
    def hide_tooltip(self):
        """Ocultar el tooltip frame."""
        if self.tooltip_frame:
            try:
                self.tooltip_frame.destroy()
            except:
                pass
            self.tooltip_frame = None



