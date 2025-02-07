import os, ctypes
import tkinter as tk
from tkinter import ttk
from session_manager import SessionManager
from systray_manager import SystrayManager
from functions import procesar_nombre

ICON = "assets/icono.ico"

class ImputacionesApp:
    def __init__(self, root):
        self.root = root
        self.toggle_state = tk.BooleanVar(value=False)
        self.selected_empresa = None

        self.configure_root()
        self.configure_styles()
        
        self.manager = SessionManager()
        
        # Pasamos la referencia de la app e iniciomos systray en un hilo
        self.systray = SystrayManager(self, ICON, "SIN USUARIO")  

        # Crear secciones de la aplicación
        self.create_user_section()
        self.create_empresa_section()
        self.create_toggle_section()
        
                
        if self.manager.logged_in:
            self.logged_in()
            

    def logged_in(self):
        self.user_label.config(text="Usuario: " + self.manager.user)
        #self.login_button.pack_forget()
        self.login_button.config(
            text="Logout",  # Cambiar el texto del botón
            bg="#e74c3c")   # Cambiar el color de fondo a rojo
    
        self.systray.update_tooltip(self.manager.user)
    
    def logged_out(self):
        self.manager.unselected_user()
        self.user_label.config(text="Usuario: No logado")
        self.login_button.config(
            text="Login",  # Cambiar el texto del botón
            bg="#2ecc71")   # Cambiar el color de fondo a rojo
        
        self.systray.update_tooltip("SIN USUARIO")
        
    def minimize_to_systray(self):
        """Oculta la ventana principal en la bandeja del sistema."""
        try:
            if self.root.winfo_exists():  # Verifica si la ventana aún existe
                self.root.withdraw()  # Oculta la ventana principal
        except Exception as e:
            print(f"Error al minimizar a la bandeja del sistema: {e}")        

    def configure_root(self):
        """Configura las propiedades de la ventana principal."""
        self.root.title("Imputaciones FrenchDesk")
        
        # Dimensiones de la ventana
        window_width = 500
        window_height = 400

        # Obtén las dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # Calcula la posición en la parte inferior derecha
        position_right = screen_width - window_width - 10
        position_bottom = screen_height - window_height - 80  # Ajustar un poco para evitar la barra de tareas
    
        # Aplica las dimensiones y posición
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_bottom}")
        self.root.configure(bg="#000000")  # Fondo negro
    
        # Definir un App User Model ID único
        myappid = "com.mycompany.myproduct.version"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.root.iconbitmap(ICON)
    
        self.minimize_to_systray()  # Ocultar la ventana al inicio
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_systray)
     
    def configure_styles(self):
        """Configura los estilos para ttk widgets."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 11, "bold"), background="#000000", foreground="#ffffff")
        style.configure("TEntry", font=("Segoe UI", 11), padding=5)
        style.configure("TCombobox", font=("Segoe UI", 11), padding=5)
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=5, relief="flat", background="#e74c3c", foreground="#ffffff")
        style.map("TButton", background=[("active", "#c0392b")])


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

    def create_user_section(self):
        """Crea la sección de usuario."""
        user_frame = tk.Frame(self.root, bg="#e74c3c", bd=2, relief="ridge")
        user_frame.pack(padx=20, pady=5, fill="x")
        self.user_label = tk.Label(user_frame, text="Usuario: No logado", font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="#ffffff")
        self.user_label.pack(side="left", padx=10)

        def handle_login_button():
            if self.manager.logged_in: self.logged_out()
            else: self.create_login_popup()
        
        self.login_button = tk.Button(
            user_frame,
            text="Login",
            font=("Segoe UI", 11, "bold"),
            bg="#2ecc71",
            fg="#ffffff",
            command=handle_login_button)
        self.login_button.pack(side="right", padx=20, pady=5)


    def create_login_popup(self):
        """Crea una ventana emergente para el login."""
        popup = tk.Toplevel(self.root)
        popup.title("Login")
        
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
        popup.configure(bg="#000000")
    
        # Agregar widgets al popup        
        tk.Label(popup, text="Usuario:", font=("Segoe UI", 11, "bold"), bg="#000000", fg="#ffffff").pack(pady=10)
        user_combobox = ttk.Combobox(popup, values=self.manager.empleados_l, state="readonly")
        user_combobox.pack(pady=5, padx=20, fill="x")
        user_combobox.current(0)

        def confirm_login():
            self.manager.selected_user(user_combobox.get())
            popup.destroy()
            self.logged_in()
    
        ttk.Button(popup, text="Entrar", command=confirm_login).pack(pady=20)


    def create_empresa_section(self):
        """Crea la sección de empresa."""
        empresa_frame = tk.Frame(self.root, bg="#e74c3c", bd=2, relief="ridge")
        empresa_frame.pack(padx=20, pady=5, fill="x")
    
        title_frame = tk.Frame(empresa_frame, bg="#e74c3c")
        title_frame.pack(anchor="w", padx=10, pady=5, fill="x")
    
        # tk.Label(title_frame, text="Empresa:", font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="#ffffff").pack(side="left")
        selected_empresa_label = tk.Label(title_frame, text="No seleccionada", font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="#ffffff")
        selected_empresa_label.pack(side="left", padx=10)
    
        cif_frame = tk.Frame(empresa_frame, bg="#e74c3c")
        cif_frame.pack(anchor="w", padx=10, pady=5, fill="x")
    
        tk.Label(cif_frame, text="CIF:", font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="#ffffff").pack(side="left")
        selected_cif_label = tk.Label(cif_frame, text="No seleccionado", font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="#ffffff")
        selected_cif_label.pack(side="left", padx=10)
    
        filter_frame = tk.Frame(empresa_frame, bg="#e74c3c")
        filter_frame.pack(anchor="w", padx=10, pady=5, fill="x")
    
        tk.Label(filter_frame, text="Filtro:", font=("Segoe UI", 11, "bold"), bg="#e74c3c", fg="#ffffff").pack(side="left")
        buscador_entry = ttk.Entry(filter_frame)
        buscador_entry.pack(side="left", fill="x", expand=True, padx=10)
    
        empresa_combobox = ttk.Combobox(empresa_frame, values=list(self.manager.empresas_dic.keys()), state="readonly")
        empresa_combobox.set("Selecciona una empresa")
        empresa_combobox.pack(fill="x", padx=10, pady=5)
    
        # Función para filtrar las empresas en el Combobox
        def filter_combobox(event):
            search_text = buscador_entry.get().lower().strip()
            words = search_text.split()  # Divide el texto en palabras
            filtered = [
                name for name, cif in self.manager.empresas_dic.items()
                if all(word in name.lower() or word in cif.lower() for word in words)  # Verifica en nombre o CIF
            ]
            empresa_combobox["values"] = filtered
            if filtered:
                empresa_combobox.set(filtered[0])
            else:
                empresa_combobox.set("")
    
        # Función para actualizar las etiquetas de empresa y CIF seleccionados
        def update_selected_label(event):
            self.selected_empresa = empresa_combobox.get()
            selected_cif = self.manager.empresas_dic.get(self.selected_empresa, "No disponible")
            selected_empresa_label.config(text=self.selected_empresa)
            selected_cif_label.config(text=selected_cif)
            self.systray.update_tooltip(self.selected_empresa)
    
        # Asociar eventos
        buscador_entry.bind("<KeyRelease>", filter_combobox)
        empresa_combobox.bind("<<ComboboxSelected>>", update_selected_label)

    def create_toggle_section(self):
        """Crea la sección del botón ON/OFF y contador."""
        toggle_frame = tk.Frame(self.root, bg="#e74c3c", bd=2, relief="ridge")
        toggle_frame.pack(padx=20, pady=5, fill="x")

        timer_label = tk.Label(toggle_frame, text="00:00:00", font=("Segoe UI", 14, "bold"), bg="#e74c3c", fg="#ffffff")
        timer_label.pack(pady=10)

        def start_timer():
            hours, minutes, seconds = 0, 0, 0

            def update_timer():
                nonlocal hours, minutes, seconds
                if self.toggle_state.get():
                    seconds += 1
                    if seconds == 60:
                        seconds = 0
                        minutes += 1
                    if minutes == 60:
                        minutes = 0
                        hours += 1
                    timer = f"{hours:02}:{minutes:02}:{seconds:02}"
                    self.systray.update_tooltip(procesar_nombre(self.manager.user) + "-->" +  self.selected_empresa + ": " + timer)
                    timer_label.config(text=timer)
                    self.root.after(1000, update_timer)

            update_timer()

        def toggle_button_action():
            if self.toggle_state.get():
                toggle_button.config(text="INICIAR", bg="#2ecc71")
                self.toggle_state.set(False)
            else:
                toggle_button.config(text="PARAR", bg="#c0392b")
                self.toggle_state.set(True)
                start_timer()

        toggle_button = tk.Button(
            toggle_frame,
            text="INICIAR",
            font=("Segoe UI", 11, "bold"),
            width=10,
            bg="#2ecc71",
            fg="#ffffff",
            command=toggle_button_action
        )
        toggle_button.pack(pady=10)

def main():
    root = tk.Tk()
    app = ImputacionesApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()