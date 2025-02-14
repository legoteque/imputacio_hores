import os, ctypes
import tkinter as tk
from tkinter import ttk
from session_manager import SessionManager
from systray_manager import SystrayManager
from functions import procesar_nombre, seconds_to_string, configure_styles
from functions import COLORES, ICON
from register import TasksAdmin



class ImputacionesApp:
    def __init__(self, root):
        self.root = root
        self._running = False
        self._paused = False
        self.elapsed_time = 0
        self.selected_empresa = None
        self.id_register = None

        # Inicialización de widgets y managers
        self.configure_root()
        configure_styles()

        self.session = SessionManager(self)
        self.systray = SystrayManager(self, ICON, "SIN USUARIO")

        # Secciones de la aplicación
        self.create_user_section()
        self.create_search_section()
        self.create_toggle_section()
        self.tasks_admin = TasksAdmin(self)
        
        self.systray.initialized.wait()  # Esperar a que el systray esté listo
        
        if self.session.logged_in:
            self.logged_in()
        else:
            self.set_logout_state()
            

#--------------------------------------------------------------------------------------------------------LOGICAL

    def handle_logout_button(self):
        if self.session.logged_in:
            #deslogamos
            self.session.unselected_user()
            self.selected_empresa = None
            self.set_logout_state()
    
    def logged_in(self):
        self.set_login_state()
        
        #cargamos el sqlite al treeview con los regostros del usuario
        self.tasks_admin.cargar_datos_desde_sqlite()
        

    # Función para actualizar las etiquetas de empresa y CIF seleccionados
    def selected_partner(self, event):
        """Lógica cuando el usuario selecciona una empresa."""
        empresa = self.empresa_combobox.get()
        
        if empresa != self.session.empresa_no_creada:
            self.selected_empresa = self.empresa_combobox.get()        
            self.set_empresa_seleccionada_state()
        else:
            self.session.añadir_empresa()
            

    
    def restored_task(self, id_registro, time, empresa, concepto):
        self.selected_empresa = empresa
        self.elapsed_time = int(time)
        self.id_register = id_registro

        self.set_empresa_seleccionada_state(time)

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
            self.timer_label.config(text=timer)
            self.systray.update_tooltip(procesar_nombre(self.session.user) + "-->" + self.selected_empresa + ": " + timer)
    
            # Convertimos id_register a str para asegurar coincidencia con el Treeview
            id_registro = str(self.id_register)
    
            if self.elapsed_time % 30 == 0:  # Actualizar solo cada 30 segundos
                self.tasks_admin.time_update(id_registro, self.elapsed_time)
                print(f"Actualizado temporizador para ID {id_registro}: {self.elapsed_time}")
    
            # Guardamos el identificador del after para poder cancelarlo si es necesario
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

        if self.running:  # Detiene el temporizador
            self.running = False
            self._paused = False
            
            #actualiza el tiempo en el treeview y db
            self.tasks_admin.time_update(self.id_register, self.elapsed_time)

            #reiniciamos valores
            self.elapsed_time = 0
            self.id_register = None
            self.selected_empresa = None
            
        else:  # Inicia el temporizador
            self.id_register = self.tasks_admin.agregar_fila(self.elapsed_time, self.selected_empresa, "")
            self.running = True
            self.update_timer()  # Inicia el temporizador


    def toggle_blinking(self, start=True):
        """Activa o desactiva el parpadeo del texto del temporizador."""
        if start:
            current_text = self.timer_label.cget("text")  # Obtiene el texto actual del label
            next_text = "" if current_text else seconds_to_string(self.elapsed_time)  # Alterna entre vacío y el tiempo actual
            self.timer_label.config(text=next_text)
            
            # Actualiza el tooltip del systray
            tooltip_text = "Pausado ⏸️" if next_text == "" else next_text
            self.systray.update_tooltip(procesar_nombre(self.session.user) + "-->" + self.selected_empresa + ": " + tooltip_text)
            
            # Programar el próximo cambio de texto en 500 ms
            self.blinking_id = self.root.after(500, lambda: self.toggle_blinking(True))
        else:
            # Detener el parpadeo y restaurar el texto original
            if hasattr(self, 'blinking_id'):
                self.root.after_cancel(self.blinking_id)
            original_text = seconds_to_string(self.elapsed_time)
            self.timer_label.config(text=original_text)  # Restaura el texto original
    
#--------------------------------------------------------------------------------------------------------GUI ROOT
     

    def configure_root(self):
        """Configura las propiedades de la ventana principal."""
        self.root.title("Imputaciones FrenchDesk")
        
        # Dimensiones de la ventana
        window_width = 800
        window_height = 600

        # Obtén las dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # Calcula la posición en la parte inferior derecha
        position_right = screen_width - window_width - 10
        position_bottom = screen_height - window_height - 80  # Ajustar un poco para evitar la barra de tareas
    
        # Aplica las dimensiones y posición
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_bottom}")
        self.root.configure(bg=COLORES["negro"])  # Fondo negro

        # Permitir redimensionamiento, pero sin botón de maximizar
        self.root.resizable(True, True)  # Permitir redimensionar manualmente
        #self.root.attributes("-toolwindow", True)  # Oculta el botón de maximizar en Windows

    
        # Definir un App User Model ID único
        myappid = "com.mycompany.myproduct.version"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.root.iconbitmap(ICON)
    
        #self.minimize_to_systray()  # Ocultar la ventana al inicio
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_systray)
        
    def minimize_to_systray(self):
        """Oculta la ventana principal en la bandeja del sistema."""
        try:
            if self.root.winfo_exists():  # Verifica si la ventana aún existe
                self.root.withdraw()  # Oculta la ventana principal
        except Exception as e:
            print(f"Error al minimizar a la bandeja del sistema: {e}")   

    def quit_application(self):
        """Función para salir completamente de la aplicación."""
        try:
            if self.systray:
                self.systray.quit_application()  # Detiene el systray
            self.root.destroy()  # Cierra la ventana de tkinter
        except Exception as e:
            print(f"Error al cerrar la aplicación: {e}")
        finally:
            os._exit(0)  # Fuerza la salida del programa


#--------------------------------------------------------------------------------------------------------GUI FRAMES
    
    def create_user_section(self):
        """Crea la sección de usuario."""
        user_frame = tk.Frame(self.root, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")
        user_frame.pack(padx=5, pady=(5,2), fill="x")
        self.user_label = ttk.Label(user_frame, text="Usuario: No logado")
        self.user_label.pack(side="left", padx=10)
        
        self.logout_button = ttk.Button(user_frame, text="Logout", style="Red.TButton", command=self.handle_logout_button)
        self.logout_button.pack(side="right", padx=20, pady=5)


    # Función para filtrar las empresas en el Combobox
    def filter_combobox(self, event):
        """Filtra las empresas en el Combobox basándose en el texto ingresado en el campo de búsqueda."""
        search_text = self.buscador_entry.get().lower().strip()
    
        # Si el campo está vacío, muestra la opción por defecto
        if not search_text:
            self.configurar_empresa_combobox(valores=list(self.session.empresas_dic.keys()), seleccion="Selecciona una empresa")
            return
    
        words = search_text.split()
        
        filtered = [name for name, cif in self.session.empresas_dic.items()
                    if all(word in name.lower() or word in cif.lower() for word in words)]

        # Eliminar la opción "empresa no creada en SUASOR" si ya existe en la lista
        if self.session.empresa_no_creada in filtered:
            filtered.remove(self.session.empresa_no_creada)

        # Asegurar que siempre aparezca la opción de "empresa no creada en SUASOR"
        filtered.append(self.session.empresa_no_creada)
    
        self.configurar_empresa_combobox(valores=filtered, seleccion=filtered[0] if filtered else self.session.empresa_no_creada)
        
    def create_search_section(self):
        """Crea la sección de búsqueda de empresa."""
        self.search_frame = tk.Frame(self.root, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")
        
        # Campo para buscar empresas
        tk.Label(self.search_frame, text="Filtro:", font=("Segoe UI", 11, "bold"), bg=COLORES["rojo_oscuro"], 
                 fg=COLORES["blanco"]).pack(side="left", padx=5)
        self.buscador_entry = ttk.Entry(self.search_frame, width=20, style="TEntry")
        self.buscador_entry.pack(side="left", padx=5, pady=5)
        
        # Combobox para seleccionar empresas
        self.empresa_combobox = ttk.Combobox(self.search_frame, values=list(self.session.empresas_dic.keys()), 
                                             style="TCombobox", state="readonly")


        # Asociar eventos
        self.buscador_entry.bind("<KeyRelease>", self.filter_combobox)
        self.empresa_combobox.bind("<<ComboboxSelected>>", self.selected_partner)

    def habilitar_buscador(self, enable=True):
        """
        Habilita o deshabilita los eventos del Combobox.
        Parámetros:
            enable (bool): Si es True, habilita los eventos; si es False, los deshabilita.
        """
        if enable:
            #self.buscador_entry.bind("<KeyRelease>", self.filter_combobox)
            self.empresa_combobox.bind("<<ComboboxSelected>>", self.selected_partner)
        else:
            #self.buscador_entry.unbind("<KeyRelease>")
            self.empresa_combobox.unbind("<<ComboboxSelected>>")

    
    def create_toggle_section(self):
        """Crea la sección del botón ON/OFF y contador usando grid."""
        self.toggle_frame = tk.Frame(self.root, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")
        
        # Configuración de las columnas en la grilla
        self.toggle_frame.grid_columnconfigure(0, weight=1, minsize=80)
        self.toggle_frame.grid_columnconfigure(1, weight=1, minsize=100)
        self.toggle_frame.grid_columnconfigure(2, weight=0, minsize=80)
        self.toggle_frame.grid_columnconfigure(3, weight=0, minsize=80)

        # Configuración de las filas dentro de toggle_frame
        self.toggle_frame.grid_rowconfigure(0, weight=1, minsize=40)  # Primera fila
        self.toggle_frame.grid_rowconfigure(1, weight=1, minsize=60)  # Segunda fila
    
        # Primera fila: Nombre de la empresa
        self.selected_empresa_label = tk.Label(self.toggle_frame, font=("Segoe UI", 14, "bold"), bg=COLORES["rojo_oscuro"], fg=COLORES["azul_claro"])
    
        # Segunda fila: CIF, temporizador y botones
        cif_label = tk.Label(self.toggle_frame, text="CIF:", font=("Segoe UI", 10, "bold"), bg=COLORES["rojo_oscuro"], fg=COLORES["azul_claro"])
        cif_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.selected_cif_label = tk.Label(self.toggle_frame, font=("Segoe UI", 10, "bold"), bg=COLORES["rojo_oscuro"], fg=COLORES["azul_claro"])
    
        # Temporizador
        self.timer_label = tk.Label(self.toggle_frame,font=("Segoe UI", 18, "bold"),bg=COLORES["rojo_oscuro"])
    
        # Botón para pausar/reanudar el temporizador
        self.pause_button = tk.Button(self.toggle_frame, font=("Segoe UI", 14, "bold"), width=3, command=lambda: self.pause_timer())
        
        # Botón para iniciar/detener el temporizador
        self.play_stop_button = tk.Button(self.toggle_frame, font=("Segoe UI", 14, "bold"), width=3, command=lambda: self.start_stop_timer())


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
        
        user_combobox = ttk.Combobox(popup, values=self.session.empleados_l, state="readonly")
        user_combobox.set("Selecciona un usuario")
        user_combobox.pack(pady=5, padx=20, fill="x")
    
        def confirm_login(event=None):
            """Se ejecuta automáticamente al seleccionar un usuario."""
            selected_user = user_combobox.get()
            if selected_user and selected_user != "Selecciona un usuario":
                self.session.selected_user(selected_user)
                popup.destroy()
                self.logged_in()
    
        # Llama a confirm_login al seleccionar un usuario
        user_combobox.bind("<<ComboboxSelected>>", confirm_login)



#-------------------------------------------------------------------------------------------------------GUI WIDGETS

    def configurar_empresa_combobox(self, mostrar=True, valores=None, seleccion=None):
        """Muestra/oculta el combobox y configura sus valores y selección si se proporcionan."""
        if mostrar:
            self.empresa_combobox.pack(fill="x", padx=5, pady=5)
            if valores is not None:
                self.empresa_combobox["values"] = valores
            if seleccion is not None:
                self.empresa_combobox.set(seleccion)
        else:
            self.empresa_combobox.pack_forget()

    def configurar_selected_empresa_label(self, mostrar=True, texto=None):
        """Muestra/oculta el label de la empresa seleccionada y actualiza su texto si se proporciona."""
        if mostrar:
            self.selected_empresa_label.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w")
            if texto is not None:
                self.selected_empresa_label.config(text=texto)
        else:
            self.selected_empresa_label.grid_remove()

    def configurar_selected_cif_label(self, mostrar=True, texto=None):
        """Muestra/oculta el label del CIF de la empresa seleccionada y actualiza su texto si se proporciona."""
        if mostrar:
            self.selected_cif_label.grid(row=1, column=0, padx=50, pady=5, sticky="w")
            if texto is not None:
                self.selected_cif_label.config(text=texto)
        else:
            self.selected_cif_label.grid_remove()

    def configurar_timer_label(self, mostrar=True, texto=None, color=None):
        """Muestra/oculta el temporizador y configura su texto y color si se proporcionan."""
        if mostrar:
            self.timer_label.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
            if texto is not None:
                self.timer_label.config(text=texto)
            if color is not None:
                self.timer_label.config(fg=color)
        else:
            self.timer_label.grid_remove()

    def configurar_pause_button(self, mostrar=True, texto=None, bg_color=None, fg_color=None, comando=None):
        """Muestra/oculta el botón de pausa y configura su texto, colores y comando si se proporcionan."""
        if mostrar:
            self.pause_button.grid(row=1, column=2, padx=(5, 2), pady=5, sticky="e")
            if texto is not None:
                self.pause_button.config(text=texto)
            if bg_color is not None:
                self.pause_button.config(bg=bg_color)
            if fg_color is not None:
                self.pause_button.config(fg=fg_color)
            if comando is not None:
                self.pause_button.config(command=comando)
        else:
            self.pause_button.grid_remove()

    def configurar_play_stop_button(self, mostrar=True, texto=None, bg_color=None, fg_color=None, comando=None):
        """Muestra/oculta el botón de inicio/detención y configura su texto, colores y comando si se proporcionan."""
        if mostrar:
            self.play_stop_button.grid(row=1, column=3, padx=(2, 5), pady=5, sticky="w")
            if texto is not None:
                self.play_stop_button.config(text=texto)
            if bg_color is not None:
                self.play_stop_button.config(bg=bg_color)
            if fg_color is not None:
                self.play_stop_button.config(fg=fg_color)
            if comando is not None:
                self.play_stop_button.config(command=comando)
        else:
            self.play_stop_button.grid_remove()


#-------------------------------------------------------------------------------------------------------GUI STATES    


    def set_logout_state(self):
        """Estado: Usuario no logueado."""
        self.user_label.config(text="Usuario: No logado")
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
        self.user_label.config(text=f"Usuario: {self.session.user} (Departamento {self.session.department.lower()})")
        self.logout_button.pack(side="right", padx=20, pady=5)
    
        # Posicionar frames
        self.search_frame.pack(padx=5, pady=2, fill="x")
        self.toggle_frame.pack(padx=5, pady=2, fill="x")
        self.tasks_admin.pack()  
        
        # Widgets dentro de search_frame
        # self.configurar_buscador_entry(mostrar=True, texto="")
        self.configurar_empresa_combobox(mostrar=True, valores=list(self.session.empresas_dic.keys()), seleccion="Selecciona una empresa")
        
        # Widgets dentro de toggle_frame
        self.configurar_selected_empresa_label(mostrar=True, texto="No seleccionada")
        self.configurar_selected_cif_label(mostrar=True, texto="-")
        
        # Reinicia contador
        self.configurar_timer_label(mostrar=False)
        self.configurar_pause_button(mostrar=False)  # Oculta el botón de pausa
        self.configurar_play_stop_button(mostrar=False)
        
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
        self.configurar_selected_empresa_label(mostrar=True, texto=self.selected_empresa)
        selected_cif = self.session.empresas_dic.get(self.selected_empresa, "No disponible")
        self.configurar_selected_cif_label(mostrar=True, texto=selected_cif)

        self.tasks_admin.treeview_manager.color_fila(color="white")
        
        if new_time is None: #No es una tarea restaurada
            self.configurar_timer_label(mostrar=True, texto="00:00:00", color=COLORES["gris_claro"])
        else:    
            self.configurar_timer_label(mostrar=True, texto=seconds_to_string(new_time), color=COLORES["gris_claro"])
            self.tasks_admin.treeview_manager.color_fila(color="yellow", id_fila=self.id_register)
            
        self.configurar_pause_button(mostrar=False)  # Oculta el botón de pausa
        self.configurar_play_stop_button(mostrar=True, texto="⏵", bg_color=COLORES["verde"],fg_color=COLORES["blanco"])
        
        self.systray.update_tooltip(self.selected_empresa)
        self.systray.update_menu_items({
            "info_partner": {"text": self.selected_empresa, "visible": True},
            "info_task": {"text": "", "visible": False},
            "info_state": {"text": "", "visible": False},
            "start_stop": {"text": "Iniciar", "visible": False}
        })

    def set_play_state(self):
        """Estado: Play (imputando tiempo)."""
        self.habilitar_buscador(False)
        
        self.configurar_timer_label(mostrar=True, color=COLORES["blanco"])
        self.configurar_play_stop_button(mostrar=True, texto="■", bg_color=COLORES["rojo"],fg_color=COLORES["blanco"])
        self.configurar_pause_button(mostrar=True, texto="||", bg_color=COLORES["gris_claro"], fg_color=COLORES["blanco"])
        
        self.tasks_admin.treeview_manager.color_fila(color="green", id_fila=self.id_register)
        self.tasks_admin.treeview_manager.habilitar_menu_contextual(False)
        self.tasks_admin.treeview_manager.habilitar_clic_izquierdo(False)
        self.tasks_admin.treeview_manager.set_all_checkboxes(" ") #dehabilitamos checkboxes
        
        self.systray.update_menu_items({
            "info_state": {"text": "🟢 Estado: Imputando", "visible": True},
            "pause": {"text": "Pausar", "visible": True},
            "start_stop": {"text": "Detener", "visible": False}
        })

    def set_pause_state(self):
        """Estado: Pausa (empresa seleccionada)."""
        self.configurar_timer_label(mostrar=True, color=COLORES["gris_claro"])
        self.configurar_play_stop_button(mostrar=True, texto="■", bg_color=COLORES["rojo"],fg_color=COLORES["blanco"])
        self.configurar_pause_button(mostrar=True, texto="⏵", bg_color=COLORES["verde_claro"], fg_color=COLORES["blanco"])
        
        self.systray.update_menu_items({
            "info_state": {"text": "⏸️ Estado: Pausado", "visible": True},
            "pause": {"text": "Reanudar", "visible": True}
        })

    def set_detener_state(self):
        """Estado: Detenido (entre tareas)."""
        self.habilitar_buscador(True)

        self.configurar_timer_label(mostrar=False)
        self.configurar_pause_button(mostrar=False)
        self.configurar_play_stop_button(mostrar=False)

        self.configurar_selected_empresa_label(mostrar=True, texto="No seleccionada")
        self.configurar_selected_cif_label(mostrar=True, texto="-")
        
        self.tasks_admin.treeview_manager.color_fila(color="white")
        self.tasks_admin.treeview_manager.habilitar_menu_contextual()
        self.tasks_admin.treeview_manager.habilitar_clic_izquierdo()

        self.systray.update_tooltip(self.session.user)
        self.systray.update_menu_items({
            "info_partner": {"visible": False},
            "info_state": {"visible": False},
            "pause": {"text": "", "visible": False},
            "start_stop": {"text": "Iniciar", "visible": False}
        })

def main():
    root = tk.Tk()
    app = ImputacionesApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
