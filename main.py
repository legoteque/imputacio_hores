import os, sys, ctypes, time
import tkinter as tk
from tkinter import ttk
from functions import CustomMessageBox as messagebox, ToolTip
from splash_screen import SplashFrame 

# Configuración inicial
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["TQDM_DISABLE"] = "True"

# Solución para evitar el error en el ejecutable
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")



def load_heavy_modules():
    """
    Importa todos los módulos pesados después del loading inicial.
    """
    global DatabaseManager, SQLServerManager, SessionManager, SystrayManager
    global BusquedaFrame, procesar_nombre, seconds_to_string
    global configure_styles, return_fecha_actual, verificar_o_crear_carpeta_archivos
    global COLORES, ICON, DB_PATH, TasksAdmin, simpledialog
    
    # Imports pesados
    from sqlite import DatabaseManager
    from sql_server import SQLServerManager
    from session_manager import SessionManager
    from systray_manager import SystrayManager
    from search_frame import BusquedaFrame
    from functions import procesar_nombre, seconds_to_string, configure_styles
    from functions import return_fecha_actual, verificar_o_crear_carpeta_archivos
    from functions import COLORES, ICON, DB_PATH
    from register import TasksAdmin
    from tkinter import simpledialog
    
    # tqdm y warnings
    from tqdm import tqdm
    tqdm_kwargs = {"file": sys.stderr}
    for i in tqdm(range(100), **tqdm_kwargs):
        pass
    
    import warnings
    warnings.simplefilter("ignore", category=UserWarning)



class ImputacionesApp:
    def __init__(self, root, splash=None, configure_styles_internally=True):
        self.root = root
        self._running = False
        self._paused = False
        self.elapsed_time = 0
        self.register_dic = None
        self.empresas_dic = {}
        self.empresas_suasor = {}

        # Verifica o crea la carpeta "archivos"
        verificar_o_crear_carpeta_archivos()
        
        # SOLO configurar estilos si se solicita explícitamente
        if configure_styles_internally:
            configure_styles()

        # --- Inicialización de instancias clave con progreso ---
        if splash:
            splash.update_message("Iniciando conexión...")
            splash.update_progress(30)
        self.sql_server_manager = SQLServerManager(self.root)

        if splash:
            splash.update_message("Cargando datos desde SUASOR...")
            splash.update_progress(50)
        self.db_manager = DatabaseManager(self, DB_PATH)

        if splash:
            splash.update_message("Inicializando sesión...")
            splash.update_progress(70)
        self.session = SessionManager(self)

        if splash:
            splash.update_message("Terminando configuración...")
            splash.update_progress(90)
        self.systray = SystrayManager(self, ICON, "SIN USUARIO")

        # Secciones de la aplicación
        self.create_user_section()
        self.search_frame = BusquedaFrame(self.root, self.session, "Buscar empresa:", self.selected_partner)
        self.create_toggle_section()
        self.tasks_admin = TasksAdmin(self)
        
        self.systray.initialized.wait()

        if self.session.logged_in:
            self.logged_in()
        else:
            self.set_logout_state()



#--------------------------------------------------------------------------------------------------------LOGICAL

    def handle_logout_button(self):
        if self.session.logged_in:
            #deslogamos
            self.session.unselected_user()
            self.register_dic = None
            self.set_logout_state()
    
    def logged_in(self):
        #cargamos todas las empresas al empresas_dic incluyendo las temporales desde las tareas del usuario
        self.empresas_suasor, self.empresas_dic = self.session.return_empresas_combo_values()
        self.conceptos_dict = self.session.return_conceptos_combo_values()

        #cargamos el sqlite al treeview con los registros del usuario
        self.tasks_admin.cargar_datos_desde_sqlite()

        #miramos y subimos si hay registros imputando (pendientes de imputar en el sqlserver) para el usuario
        self.sql_server_manager.subir_registros(self.db_manager, self.session.user_id)
        
        self.set_login_state()

    #recarga las empresas y conceptos desde la base de datos y actualiza el combobox
    def reload_empresas_combobox_update(self):
        self.empresas_suasor, self.empresas_dic = self.session.return_empresas_combo_values()
        self.search_frame.configurar_combobox(self.empresas_dic, seleccion="Selecciona una empresa")
        self.conceptos_dict = self.session.return_conceptos_combo_values()

    
    def actualizar_datos_desde_servidor(self):
        """Función para actualizar datos desde SQL Server desde el botón del header."""
        if hasattr(self, 'session') and self.session:
            self.session.actualizar_datos_desde_servidor()
        else:
            messagebox.showerror("Error", "No hay sesión activa para actualizar datos.")


    # Función para actualizar las etiquetas de empresa y CIF seleccionados
    def selected_partner(self, event):
        """Lógica cuando el usuario selecciona una empresa."""
        #deseleccionamos cualquier registro del treeview
        self.tasks_admin.treeview_manager.deseleccionar_fila()

        empresa = self.search_frame.combobox.get()
        
        if empresa != self.session.empresa_no_creada:
            self.register_dic = {"empresa": self.search_frame.combobox.get()}
            selected_cif = self.empresas_dic.get(self.register_dic["empresa"], "No disponible")
            self.register_dic["cif"] = selected_cif
            #comprobamos si existe el par empresa cif en empresas_suasor
            if self.empresas_suasor.get(self.register_dic["empresa"]) == self.register_dic["cif"]:
                self.register_dic["vinculada"] = True
            else:
                self.register_dic["vinculada"] = False
        else:
            nueva_empresa, nuevo_cif = self.new_partner()
            self.register_dic = {"empresa": nueva_empresa}
            self.register_dic["cif"] = nuevo_cif
            self.register_dic["vinculada"] = False

        self.register_dic["concepto"], self.register_dic["descripcion"] = "", ""
        self._running = False
        self._paused = False
        self.elapsed_time = 0

        self.set_empresa_seleccionada_state()

    def unselected_partner(self):
        """Logica cuando se realiza cualquier accion que nos lleva a deseleccionar la empresa activa"""
        #deseleccionamos cualquier registro del treeview
        self.tasks_admin.treeview_manager.deseleccionar_fila()
        #reiniciamos valores
        self._running = False
        self._paused = False
        self.elapsed_time = 0
        self.register_dic = None
        self.reload_empresas_combobox_update()
        self.set_detener_state()
            

    def new_partner(self):
        """
        Abre cuadros de diálogo para ingresar una nueva empresa y su número de identificación fiscal (VAT),
        y la guarda en el CSV.
        """
        # Pedir nombre de la empresa
        nueva_empresa = simpledialog.askstring("Nueva Empresa", "Ingrese el nombre de la nueva empresa:", parent=self.root).strip()
        if not nueva_empresa: return
        nueva_empresa = nueva_empresa.strip().upper()  # Normalizar a mayúsculas

         # Verificar si el nombre ya existe
        if nueva_empresa in self.empresas_dic.keys():
            cif_existente = self.empresas_dic[nueva_empresa]  # Obtener el CIF asociado
            messagebox.showerror("Error", f"La empresa '{nueva_empresa}' ya existe en el listado de empresas seleccionables con el CIF '{cif_existente}'.", 
                                 parent=self.root)
            return

        # Pedir número VAT
        nuevo_cif = simpledialog.askstring("Número VAT", "Ingrese el número de identificación fiscal (CIF):", parent=self.root).strip()
        if not nuevo_cif: return
        nuevo_cif = nuevo_cif.strip().upper()  # Normalizar a mayúsculas

        # Verificar si el VAT ya existe
        if nuevo_cif in self.empresas_dic.values():
            empresa_existente = [key for key, value in self.empresas_dic.items() if value == nuevo_cif][0]
            messagebox.showerror("Error", f"El CIF '{nuevo_cif}' ya existe en el listado de empresas seleccionables para la empresa '{empresa_existente}'.", 
                                 parent=self.root)
            return

        return nueva_empresa, nuevo_cif

    
    def restored_task(self, register_dic):
        self.register_dic = register_dic
        self.elapsed_time = int(register_dic["tiempo"])

        self.set_empresa_seleccionada_state(self.elapsed_time)

        self._running = True
        self.paused = True
        


    @property
    def running(self):
        """Getter de la variable."""
        return self._running
    @running.setter
    def running(self, value):
        """GUI que se establece cuando running cambia."""
        self._running = value
        
        if self._running:
            self.set_play_state()
        else:
            self.set_detener_state()

    @property
    def paused(self):
        return self._paused
    @paused.setter
    def paused(self, value):
        """GUI para pausar/reanudar el temporizador."""
        self._paused = value  # <--- Usamos la variable privada
        if self._paused:
            self.set_pause_state()
        else:
            self.set_play_state()


    def update_timer(self):
        """Actualiza el temporizador cada segundo mientras está en marcha."""
        if self._running and not self._paused:  # Solo si está en marcha y no en pausa
            self.elapsed_time += 1
            timer = seconds_to_string(self.elapsed_time)
            self.widgets["timer_label"].config(text=timer)
            self.systray.update_tooltip(procesar_nombre(self.session.user) + "-->" + self.register_dic["empresa"] + ": " + timer)
    
            # Convertimos id a str para asegurar coincidencia con el Treeview
            id_registro = str(self.register_dic["id"])
    
            if self.elapsed_time % 30 == 0:  # Actualizar solo cada 30 segundos
                #captura los valores de concepto y descripcion
                concepto_descripcion = self.widgets["selected_concepto_combobox"].get()
                if concepto_descripcion and hasattr(self, 'conceptos_dict'):
                    self.register_dic["concepto"] = self.conceptos_dict.get(concepto_descripcion, "")
                else:
                    self.register_dic["concepto"] = ""
                self.register_dic["descripcion"] = self.widgets["selected_descripcion_entry"].get()
                self.tasks_admin.update_register(self.register_dic, self.elapsed_time)
    
            # Guardamos el identificador del after para poder cancelarlo
            self.timer_id = self.root.after(1000, self.update_timer)

            
    def pause_timer(self):
        """Pausa o reanuda el temporizador."""
        self.paused = not self._paused  # Alterna entre pausa y reanudación
        if self._paused:
            self.root.after_cancel(self.timer_id)  # Cancela el temporizador activo
            self.toggle_blinking()
        else:
            self.toggle_blinking(False)
            self.update_timer()  # Reanuda el temporizador


    def start_stop_timer(self):
        """Maneja la lógica de iniciar y detener el temporizador."""

        # Detener el parpadeo siempre
        self.toggle_blinking(False)

        # 🔹 CAPTURAR VALORES CORRECTAMENTE
        # Convertir descripción a código para concepto
        concepto_descripcion = self.widgets["selected_concepto_combobox"].get()
        if concepto_descripcion and hasattr(self, 'conceptos_dict'):
            self.register_dic["concepto"] = self.conceptos_dict.get(concepto_descripcion, "")
        else:
            self.register_dic["concepto"] = ""
        
        self.register_dic["descripcion"] = self.widgets["selected_descripcion_entry"].get()
        
        if self.running:  # Detiene el temporizador
            tarea_interna = self.register_dic.get("empresa", "").startswith('0')
            if not tarea_interna and not self.register_dic.get("concepto", ""):
                messagebox.showerror("Concepto requerido", 
                                "Debe seleccionar un concepto para esta empresa.\n"
                                "Solo las tareas internas pueden no tener concepto.")
                return  # Salir sin detener el temporizador

            self.running = False
            self._paused = False

            #actualiza el tiempo y datos de entrys en el treeview y db
            self.tasks_admin.update_register(self.register_dic, self.elapsed_time)

            #reiniciamos valores
            self.elapsed_time = 0
            self.register_dic = None
            
        else:  # Inicia el temporizador
            if self.elapsed_time == 0: #nou registre
                self.register_dic["fecha_creacion"] = return_fecha_actual()
                self.register_dic["id"] = self.tasks_admin.nuevo_registro(self.elapsed_time, self.register_dic)
                #actualiza el tiempo y datos de entrys en el treeview y db
                self.tasks_admin.update_register(self.register_dic, self.elapsed_time)

            self.running = True
            self.update_timer()  # Inicia el temporizador




    def toggle_blinking(self, start=True):
        """Activa o desactiva el parpadeo del texto del temporizador."""
        if start:
            current_text = self.widgets["timer_label"].cget("text")  # Obtiene el texto actual del label
            next_text = "" if current_text else seconds_to_string(self.elapsed_time)  # Alterna entre vacío y el tiempo actual
            self.widgets["timer_label"].config(text=next_text)
            
            # Actualiza el tooltip del systray
            tooltip_text = "Pausado ⏸️" if next_text == "" else next_text
            self.systray.update_tooltip(procesar_nombre(self.session.user) + "-->" + self.register_dic["empresa"] + ": " + tooltip_text)
            
            # Programar el próximo cambio de texto en 500 ms
            self.blinking_id = self.root.after(500, lambda: self.toggle_blinking(True))
        else:
            # Detener el parpadeo y restaurar el texto original
            if hasattr(self, 'blinking_id'):
                self.root.after_cancel(self.blinking_id)
            original_text = seconds_to_string(self.elapsed_time)
            self.widgets["timer_label"].config(text=original_text)  # Restaura el texto original
    
#--------------------------------------------------------------------------------------------------------GUI ROOT
     

    def configure_root(self):
        """Configura la ventana básica."""
        
        # ✅ RESTAURAR BARRA DE TÍTULO (crucial después del splash)
        self.root.overrideredirect(False)
        
        # Título de la ventana
        self.root.title("Imputaciones FrenchDesk")
        
        # Dimensiones y posición
        window_width = 1100
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_right = screen_width - window_width - 10
        position_bottom = screen_height - window_height - 80
        
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_bottom}")
        self.root.configure(bg=COLORES["negro"])
        
        try:
            # Configurar icono
            self.root.iconbitmap(ICON)
            
            # ✅ App ID para que aparezca correctamente en la barra de tareas
            myappid = "com.frenchdesk.imputaciones.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
        except Exception as e:
            print(f"Advertencia: Configuración básica de ventana: {e}")
        
        # Habilitar redimensionamiento
        self.root.resizable(True, True)



    def minimize_to_systray(self):
        """Oculta la ventana principal en la bandeja del sistema."""
        try:
            if self.root.winfo_exists():
                self.root.withdraw()
        except Exception as e:
            pass


    def minimize_to_taskbar(self):
        """Minimiza la ventana normalmente."""
        try:
            self.root.iconify()
        except:
            self.root.withdraw()

    def quit_application(self):
        """Función para salir completamente de la aplicación."""
        try:
            if self.systray:
                self.systray.quit_application()
            self.root.destroy()
        except Exception as e:
            pass
        finally:
            os._exit(0)



    def make_draggable(self, widget):
        """Hace que la ventana sea arrastrable desde un widget específico."""
        def start_drag(event):
            widget.start_x = event.x
            widget.start_y = event.y

        def do_drag(event):
            x = self.root.winfo_x() + (event.x - widget.start_x)
            y = self.root.winfo_y() + (event.y - widget.start_y)
            self.root.geometry(f"+{x}+{y}")

        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", do_drag)

    def setup_window_dragging(self):
        """Configura el arrastre de ventana en el header_frame."""
        # Hacer el header arrastrable (se llamará después de crear el header_frame)
        if hasattr(self, 'header_frame'):
            self.make_draggable(self.header_frame)
            # También hacer arrastrable el user_label para más área de arrastre
            if hasattr(self, 'user_label'):
                self.make_draggable(self.user_label)


    
#--------------------------------------------------------------------------------------------------------GUI FRAMES
    

    def create_user_section(self):
        """Crea la sección header solo con usuario y logout."""
        
        # Header frame principal
        self.header_frame = tk.Frame(self.root, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")
        self.header_frame.pack(padx=5, pady=(5,2), fill="x")
        
        # User frame (lado izquierdo)
        user_frame = tk.Frame(self.header_frame, bg=COLORES["rojo_oscuro"])
        user_frame.pack(side="left", expand=False)
        
        # Label del usuario
        self.user_label = ttk.Label(user_frame, text="Usuario no logado", style="Main.TLabel")
        self.user_label.pack(side="left", padx=(10, 0), pady=5)
        
        # Botón de logout
        self.logout_button = ttk.Button(user_frame, text="Logout", style="Logout.TButton", 
                                    command=self.handle_logout_button)
        self.logout_button.pack(side="left", padx=(0, 0), pady=5)
        
        # Buttons frame (lado derecho)
        buttons_frame = tk.Frame(self.header_frame, bg=COLORES["rojo_oscuro"])
        buttons_frame.pack(side="right", padx=(5, 10), pady=5)

        # ✅ BOTÓN DE INSERTAR MANUAL MEJORADO
        self.insertar_button = ttk.Button(buttons_frame, text="📝 Entrada Registos", 
                                        style="Insert.TButton", command=self.abrir_insercion_manual,
                                        cursor="hand2")
        self.insertar_button.pack(side="right", padx=(8, 0), pady=2)

        # ✅ CREAR TOOLTIP PARA EL BOTÓN DE INSERTAR
        ToolTip(self.insertar_button, "Inserción Manual de Registros\nCrear nuevos registros de tiempo manualmente")
        
        # ✅ BOTÓN DE ACTUALIZAR MEJORADO
        self.refresh_button = ttk.Button(buttons_frame, text="🔄 Actualizar desde SUASOR", 
                                    style="Sync.TButton", command=self.actualizar_datos_desde_servidor,
                                    cursor="hand2")
        self.refresh_button.pack(side="right", padx=(8, 0), pady=2)
        
        # ✅ CREAR TOOLTIP PARA EL BOTÓN DE SINCRONIZAR
        ToolTip(self.refresh_button, "Sincronizar con Servidor\nActualiza empleados, empresas y conceptos desde SQL Server")
        
        # Arrastre opcional
        self.setup_window_dragging()


    # ✅ AÑADIR MÉTODO PARA MANEJAR EL BOTÓN DE INSERTAR
    def abrir_insercion_manual(self):
        """Abre la ventana de inserción manual de registros."""
        if hasattr(self, 'session') and self.session.logged_in:
            # Solo permitir si hay usuario logueado
            if hasattr(self, 'tasks_admin'):
                self.tasks_admin.insercion_manual()
            else:
                messagebox.showerror("Error", "El sistema de tareas no está inicializado.")
        else:
            messagebox.showwarning("Sin usuario", "Debe iniciar sesión para insertar registros.")


    def create_toggle_section(self):
        """Crea la sección del botón ON/OFF y contador con todos los widgets colgando de toggle_frame."""
        
        self.toggle_frame = tk.Frame(self.root, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")

        # Diccionario de widgets para facilitar manipulación
        self.widgets = {}

        # 🟢 Fila 0: Empresa + CIF
        self.widgets["selected_empresa_label"] = ttk.Label(self.toggle_frame, style="Main.TLabel")
        
        self.widgets["cif_frame"] = tk.Frame(self.toggle_frame, bg=COLORES["rojo_oscuro"])  # Contenedor para CIF
        self.widgets["cif_label"] = ttk.Label(self.widgets["cif_frame"], text="CIF:", style="TLabel")
        self.widgets["selected_cif_label"] = ttk.Label(self.widgets["cif_frame"], font=("Courier", 13, "bold"), foreground="black", width=10)
        
        self.widgets["cif_label"].grid(row=0, column=0, padx=2, sticky="w")
        self.widgets["selected_cif_label"].grid(row=0, column=1, padx=5, sticky="w")

        # 🔵 Fila 1: Labels de Concepto y Descripción (en la misma columna)
        self.widgets["labels_frame"] = tk.Frame(self.toggle_frame, bg=COLORES["rojo_oscuro"])  # Contenedor para labels
        
        self.widgets["concepto_label"] = ttk.Label(self.widgets["labels_frame"], text="Concepto:")
        self.widgets["descripcion_label"] = ttk.Label(self.widgets["labels_frame"], text="Descripción:")
        
        self.widgets["concepto_label"].grid(row=0, column=0, padx=2, pady=2, sticky="w")
        self.widgets["descripcion_label"].grid(row=1, column=0, padx=2, pady=2, sticky="w")

        # 🔵 Fila 1: Inputs de Concepto y Descripción (en la misma columna)
        self.widgets["inputs_frame"] = tk.Frame(self.toggle_frame, bg=COLORES["rojo_oscuro"])  # Contenedor para inputs
        
        self.widgets["selected_concepto_combobox"] = ttk.Combobox(self.widgets["inputs_frame"], justify="left", 
                                                                font=("Courier", 9, "bold"), foreground="black", state="readonly")
        self.widgets["selected_descripcion_entry"] = ttk.Entry(self.widgets["inputs_frame"], justify="left", 
                                                            font=("Courier", 9, "bold"), foreground="black")
        
        self.widgets["selected_concepto_combobox"].grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.widgets["selected_descripcion_entry"].grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        
        self.widgets["inputs_frame"].grid_columnconfigure(0, weight=1)  # Los inputs se estiran

        # 🔴 Fila 2: Botones (como estaba)
        self.widgets["buttons_frame"] = tk.Frame(self.toggle_frame, bg=COLORES["rojo_oscuro"]) # Contenedor para Buttons
        self.widgets["buttons_frame"].grid_columnconfigure(0, weight=1, minsize=80)
        self.widgets["buttons_frame"].grid_columnconfigure(1, weight=0, minsize=60)
        self.widgets["buttons_frame"].grid_columnconfigure(2, weight=0, minsize=60)

        self.widgets["timer_label"] = ttk.Label(self.widgets["buttons_frame"], width=10, style="Timer.TLabel")
        self.widgets["pause_button"] = ttk.Button(self.widgets["buttons_frame"], width=3, style="Pause.TButton", command=lambda: self.pause_timer())
        self.widgets["play_stop_button"] = ttk.Button(self.widgets["buttons_frame"], width=3, style="Play.TButton", command=lambda: self.start_stop_timer())

        # Organizar dentro del buttons_frame
        self.widgets["timer_label"].grid(row=0, column=0, padx=7, sticky="w")
        self.widgets["pause_button"].grid(row=0, column=1, padx=1, sticky="w")
        self.widgets["play_stop_button"].grid(row=0, column=2, padx=1, sticky="w")

        # 🔹 Layout NUEVO de los widgets
        layout = [
            # Fila 0: Empresa (3 columnas) + CIF (última columna a la derecha)
            ("selected_empresa_label", 0, 0, 3, "w"),
            ("cif_frame", 0, 3, 1, "e"),

            # Fila 1: Labels (1 columna) + Inputs (2 columnas) + Botones (1 columna)
            ("labels_frame", 1, 0, 1, "w"),
            ("inputs_frame", 1, 1, 2, "ew"),
            ("buttons_frame", 1, 3, 1, "w"),
        ]

        # 🔹 Configurar columnas y filas dinámicamente
        for i in range(2): 
            self.toggle_frame.grid_rowconfigure(i, weight=1, minsize=40)

        self.toggle_frame.grid_columnconfigure(0, weight=0, minsize=100)  # Labels
        self.toggle_frame.grid_columnconfigure(1, weight=1, minsize=200)  # Inputs (se estiran)
        self.toggle_frame.grid_columnconfigure(2, weight=1, minsize=200)  # Inputs continúa
        self.toggle_frame.grid_columnconfigure(3, weight=0, minsize=120)  # CIF + Botones

        # 🔹 Aplicar layout a cada widget
        for widget_name, row, col, colspan, sticky in layout:
            self.widgets[widget_name].grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky=sticky)

    def configurar_hover_play_stop(self, activar=True):
        """Activa o desactiva el efecto hover en play_stop_button."""
        if activar:
            self.widgets["play_stop_button"].bind("<Enter>", lambda e: self.widgets["play_stop_button"].config(text="⬇"))
            self.widgets["play_stop_button"].bind("<Leave>", lambda e: self.widgets["play_stop_button"].config(text="■"))
        else:
            self.widgets["play_stop_button"].unbind("<Enter>")
            self.widgets["play_stop_button"].unbind("<Leave>")



    def create_login_popup(self):
        """Crea una ventana emergente para el login."""
        popup = tk.Toplevel(self.root)
        popup.title("Login")
    
        popup.overrideredirect(True)  # Elimina decoraciones (barra de título, botones de control)
        popup.grab_set()  # Bloquea la interacción con la ventana principal
        popup.attributes("-topmost", True)  # Asegura que el popup se mantenga en primer plano
        
        # Dimensiones de la ventana emergente
        popup_width = 300
        popup_height = 200
    
        # Obtén las dimensiones de la ventana principal
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
    
        # Calcula la posición centrada
        position_x = root_x + (root_width - popup_width) // 2
        position_y = root_y + (root_height - popup_height) // 2
    
        # Establece la geometría con las posiciones calculadas
        popup.geometry(f"{popup_width}x{popup_height}+{position_x}+{position_y}")
        popup.configure(bg=COLORES["negro"])
    
        # Agregar widgets al popup        
        tk.Label(popup, text="Usuario:", font=("Segoe UI", 11, "bold"), bg=COLORES["negro"], fg=COLORES["blanco"]).pack(pady=10)
        
        user_combobox = ttk.Combobox(popup, values=list(self.session.empleados_dict.keys()), state="readonly")
        user_combobox.set("Selecciona un usuario")
        user_combobox.pack(pady=5, padx=20, fill="x")
    
        def confirm_login(event=None):
            """Se ejecuta automáticamente al seleccionar un usuario."""
            selected_user = user_combobox.get()
            if selected_user and selected_user != "Selecciona un usuario":
                self.session.selected_user(self.session.empleados_dict[selected_user], selected_user)
                popup.destroy()
                self.logged_in()
    
        # Llama a confirm_login al seleccionar un usuario
        user_combobox.bind("<<ComboboxSelected>>", confirm_login)



#-------------------------------------------------------------------------------------------------------GUI WIDGETS


    def configurar_label(self, widget, mostrar=True, texto=None, estilo=None):
        if mostrar:
            self.widgets[widget].grid()
            if texto is not None:
                if isinstance(self.widgets[widget], ttk.Entry):
                    self.widgets[widget].delete(0, tk.END)
                    self.widgets[widget].insert(0, texto)
                elif isinstance(self.widgets[widget], ttk.Combobox):
                    self.widgets[widget].set(texto)  # Solo para casos simples
                else:
                    self.widgets[widget].config(text=texto)
            if estilo is not None:
                self.widgets[widget].config(style=estilo)
        else:
            self.widgets[widget].grid_remove()

   
    def configurar_button(self, button, mostrar=True, estilo=None, comando=None):
        """Muestra/oculta el botón de inicio/detención y configura su texto, colores y comando si se proporcionan."""
        if mostrar:
            self.widgets[button].grid()

            if estilo is not None:
                self.widgets[button].config(style=estilo)

                if estilo == "Play.TButton": #boton play
                    texto = "⏵"
                    self.configurar_hover_play_stop(activar=False)
                elif estilo == "Stop.TButton": #boton detener
                    texto = "■"
                    self.configurar_hover_play_stop(activar=True)
                elif estilo == "Pause.TButton": #boton pause
                    texto = "||"
                elif estilo == "Reanudar.TButton": #boton reanudar
                    texto = "⏵"
                self.widgets[button].config(text=texto)
                
            if comando is not None:
                self.widgets[button].config(command=comando)
        else:
            self.widgets[button].grid_remove()


#-------------------------------------------------------------------------------------------------------GUI STATES    


    def set_logout_state(self):
        """Estado: Usuario no logueado."""
        self.user_label.config(text="Usuario no logado")
        self.logout_button.pack_forget()
        
        self.search_frame.pack_forget()
        self.toggle_frame.pack_forget()
        self.tasks_admin.pack_forget()

        self.create_login_popup()
        
        self.systray.update_tooltip("SIN USUARIO")
        self.systray.update_menu_items({
            "info_user": {"text": "Usuario No logado"},
            "info_partner": {"text": "", "visible": False},
            "info_task": {"text": "", "visible": False},
            "info_state": {"text": "", "visible": False},
            "pause": {"visible": False},
            "start_stop": {"visible": False}
        }) 

    def set_login_state(self):
        """Estado: Usuario logueado, configuración inicial."""
        self.user_label.config(text=f"{self.session.user} (Departamento {self.session.department.lower()})")
        self.logout_button.pack(side="right", padx=20, pady=5)
    
        # Posicionar frames
        self.search_frame.pack(padx=5, pady=2, fill="x")
        self.toggle_frame.pack(padx=5, pady=2, fill="x")
        self.tasks_admin.pack()
        
        # Widgets dentro de search_frame
        self.search_frame.configurar_combobox(self.empresas_dic, seleccion="Selecciona una empresa")
        
        # Widgets dentro de toggle_frame
        self.configurar_label(widget= "selected_empresa_label", mostrar=True, texto="No seleccionada")
        self.configurar_label(widget= "selected_cif_label", mostrar=True, texto="-")

        # 🔹 AGREGAR: Deshabilitar campos concepto y descripción
        self.widgets["selected_concepto_combobox"]["values"] = list(self.conceptos_dict.keys())
        self.widgets["selected_concepto_combobox"].config(state="disabled")
        self.widgets["selected_descripcion_entry"].config(state="disabled")
            
        # Reinicia contador
        self.configurar_label(widget="timer_label", mostrar=False)
        self.configurar_button(button="pause_button", mostrar=False)  # Oculta el botón de pausa
        self.configurar_button(button="play_stop_button", mostrar=False)
        
        # Actualiza systray
        self.systray.update_tooltip(self.session.user)
        self.systray.update_menu_items({
            "info_user": {"text": self.session.user},
            "info_partner": {"text": "", "visible": False},
            "info_task": {"text": "", "visible": False},
            "info_state": {"text": "", "visible": False},
            "pause": {"visible": False},
            "start_stop": {"visible": False}
        })

    def set_empresa_seleccionada_state(self, new_time=None):
        """Estado: Empresa seleccionada, contador detenido."""

        self.configurar_label(widget="selected_empresa_label", mostrar=True, texto=self.register_dic["empresa"])
        self.configurar_label(widget="selected_cif_label", mostrar=True, texto=self.register_dic["cif"])

        self.tasks_admin.treeview_manager.color_fila(color="white") #todas las filas en blanco
        
        if new_time is None: #No es una tarea restaurada
            text = "00:00:00"
        else:    
            text = seconds_to_string(new_time)
            self.tasks_admin.treeview_manager.color_fila(color="yellow", id_fila=self.register_dic["id"]) #amarillo el id seleccionado
        
        
         # 🔹 HABILITAR COMBOBOX DE CONCEPTOS Y CONFIGURAR VALORES
        self.widgets["selected_concepto_combobox"].config(state="readonly")
        
        # Buscar la descripción que corresponde al código almacenado
        concepto_codigo = self.register_dic["concepto"]
        concepto_descripcion = ""
        
        if concepto_codigo and hasattr(self, 'conceptos_dict'):
            # Buscar por valor (código) para obtener la clave (descripción)
            for desc, codigo in self.conceptos_dict.items():
                if codigo == concepto_codigo:
                    concepto_descripcion = desc
                    break

        # Configurar directamente el combobox
        self.widgets["selected_concepto_combobox"].set(concepto_descripcion)
        
        # 🔹 HABILITAR DESCRIPCIÓN
        self.widgets["selected_descripcion_entry"].config(state="normal")
        self.configurar_label(widget="selected_descripcion_entry", texto=self.register_dic["descripcion"])



        self.configurar_label(widget="timer_label", mostrar=True, texto=text, estilo="PTimer.TLabel")
            
        self.configurar_button(button="pause_button", mostrar=False)  # Oculta el botón de pausa
        self.configurar_button(button="play_stop_button", mostrar=True, estilo="Play.TButton")
        
        self.systray.update_tooltip(self.register_dic["empresa"])
        self.systray.update_menu_items({
            "info_partner": {"text": self.register_dic["empresa"], "visible": True},
            "info_task": {"text": "", "visible": False},
            "info_state": {"text": "", "visible": False},
            "start_stop": {"text": "Iniciar", "visible": False}
        })

    def set_play_state(self):
        """Estado: Play (imputando tiempo)."""
        self.search_frame.habilitar_seleccion(False)

        #si es una empresa creada recargamos empresas_dic de la base de datos y actualizamos el combobox
        if not self.register_dic["vinculada"]:
            self.reload_empresas_combobox_update()
        
        self.configurar_label(widget="timer_label", mostrar=True, estilo="Timer.TLabel")
        self.configurar_button(button="play_stop_button", mostrar=True, estilo="Stop.TButton")
        self.configurar_button(button="pause_button", mostrar=True, estilo="Pause.TButton")
        
        self.tasks_admin.treeview_manager.color_fila(color="green", id_fila=self.register_dic["id"])
        self.tasks_admin.treeview_manager.habilitar_interaccion_treeview(False)
        self.tasks_admin.treeview_manager.set_all_checkboxes(" ") #dehabilitamos checkboxes
        
        self.systray.update_menu_items({
            "info_state": {"text": "🟢 Estado: Imputando", "visible": True},
            "pause": {"text": "Pausar", "visible": True},
            "start_stop": {"text": "Detener", "visible": False}
        })

    def set_pause_state(self):
        """Estado: Pausa (empresa seleccionada)."""
        self.configurar_label(widget="timer_label", mostrar=True, estilo="PTimer.TLabel")
        self.configurar_button(button="play_stop_button", mostrar=True, estilo="Stop.TButton")
        self.configurar_button(button="pause_button", mostrar=True, estilo="Reanudar.TButton")
        
        self.systray.update_menu_items({
            "info_state": {"text": "⏸️ Estado: Pausado", "visible": True},
            "pause": {"text": "Reanudar", "visible": True}
        })

    def set_detener_state(self):
        """Estado: Detenido (entre tareas)."""
        self.search_frame.habilitar_seleccion(True)

        self.configurar_label(widget="timer_label", mostrar=False)
        self.configurar_button(button="pause_button", mostrar=False)
        self.configurar_button(button="play_stop_button", mostrar=False)

        self.configurar_label(widget="selected_empresa_label", mostrar=True, texto="No seleccionada")
        self.configurar_label(widget="selected_cif_label", mostrar=True, texto="-")
        
        # 🔹 LIMPIAR COMBOBOX EXPLÍCITAMENTE
        self.widgets["selected_concepto_combobox"].set("")  # Forzar limpieza
        self.configurar_label(widget="selected_concepto_combobox", mostrar=True, texto="")
        
        self.configurar_label(widget="selected_descripcion_entry", mostrar=True, texto="")
        
        # 🔹 DESHABILITAR CAMPOS DESPUÉS DE LIMPIARLOS
        self.widgets["selected_concepto_combobox"].config(state="disabled")
        self.widgets["selected_descripcion_entry"].config(state="disabled")
            
        self.tasks_admin.treeview_manager.color_fila(color="white")
        self.tasks_admin.treeview_manager.habilitar_interaccion_treeview()

        self.systray.update_tooltip(self.session.user)
        self.systray.update_menu_items({
            "info_partner": {"visible": False},
            "info_state": {"visible": False},
            "pause": {"text": "", "visible": False},
            "start_stop": {"text": "Iniciar", "visible": False}
        })




def main():
    # 1️⃣ Crear UNA SOLA ventana root desde el principio
    root = tk.Tk()
    root.title("Imputaciones FrenchDesk")
    root.geometry("400x200")
    root.resizable(False, False)
    
    # ✅ QUITAR BARRA DE TÍTULO DEL SPLASH
    root.overrideredirect(True)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - 200
    y = (root.winfo_screenheight() // 2) - 100
    root.geometry(f"400x200+{x}+{y}")
    
    # 2️⃣ Crear splash como Frame dentro de root
    splash_frame = SplashFrame(root)
    
    def load_and_start():
        try:
            # 3️⃣ Cargando módulos
            splash_frame.update_message("Cargando módulos...")
            splash_frame.update_progress(10)
            load_heavy_modules()
            
            # 4️⃣ Configurar estilos INMEDIATAMENTE en root limpio
            splash_frame.update_message("Configurando estilos...")
            splash_frame.update_progress(20)
            configure_styles()
            
            # 5️⃣ Crear aplicación usando el MISMO root
            splash_frame.update_message("Iniciando conexión...")
            splash_frame.update_progress(30)
            
            # Crear la app sin splash (porque ya tenemos el splash_frame)
            app = ImputacionesApp(root, splash=splash_frame, configure_styles_internally=False)
            app.configure_root()

            # 6️⃣ Destruir el splash frame y redimensionar ventana
            splash_frame.update_message("¡Listo!")
            splash_frame.update_progress(100)
            time.sleep(0.3)
            splash_frame.destroy_splash()
            
            # Redimensionar ventana para la aplicación final
            window_width = 1100
            window_height = 600
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            position_right = screen_width - window_width - 10
            position_bottom = screen_height - window_height - 80
            root.geometry(f"{window_width}x{window_height}+{position_right}+{position_bottom}")
            root.resizable(True, True)
            
            root.mainloop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar la aplicación:\n{e}")
            sys.exit(1)
    
    # 7️⃣ Iniciar carga después de mostrar splash
    root.after(300, load_and_start)
    root.mainloop()

if __name__ == "__main__":
    main()