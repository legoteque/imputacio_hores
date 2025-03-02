from pystray import Icon, Menu, MenuItem
from PIL import Image
import threading


class SystrayManager:
    def __init__(self, app, icon_path, tooltip_text):
        """Inicializa el systray y conecta con la aplicación principal."""
        self.app = app
        self.icon_path = icon_path
        self.tooltip_text = tooltip_text  # Texto inicial del tooltip
        self.icon = None
        self.initialized = threading.Event()  # Evento para sincronización
        self.menu_items = {}  # Almacena referencias a los items del menú

        # Crear el systray en un hilo separado
        systray_thread = threading.Thread(target=self.create_systray, daemon=True)
        systray_thread.start()

    def create_systray(self):
        """Crea el ícono del systray con su menú."""

         # Definir las acciones asociadas a los ítems
        self.menu_actions = {
            "info_user": None,  # Ítem no clicable
            "info_partner": None,  # Ítem no clicable
            "info_task": None,  # Ítem no clicable
            "info_state": None,  # Ítem no clicable
            "separator": None,  # Ítem separador
            "toggle_window": self.toggle_app_window,
            "pause": self.app.pause_timer,
            "start_stop": lambda icon, item: self.app.root.after(0, self.app.start_stop_timer),
            #"start_stop": self.app.start_stop_timer,
            "quit": self.quit_application,
        }

        # Crear los ítems del menú
        self.menu_items = {
            "info_user": MenuItem("Empleado: No iniciado", None, enabled=False),
            "info_partner": MenuItem("", None, enabled=False, visible=False),
            "info_task": MenuItem("", None, enabled=False, visible=False),
            "info_state": MenuItem("", None, enabled=True, visible=False),
            "separator": MenuItem("", None, enabled=False),  # Separador
            "toggle_window": MenuItem("Alternar ventana", self.menu_actions["toggle_window"], 
                                      default=True, visible=False),
            "pause": MenuItem("Pausar", self.menu_actions["pause"], visible=False),
            "start_stop": MenuItem("Iniciar", self.menu_actions["start_stop"], visible=False),
            "quit": MenuItem("Salir", self.menu_actions["quit"]),
        }

        # Crear el menú con los ítems
        menu = Menu(*self.menu_items.values())

        # Cargar el ícono
        try:
            icon_image = Image.open(self.icon_path)
        except Exception as e:
            #print(f"Error al cargar el ícono: {e}")
            return  # Salir de la función si el ícono no se carga

        # Crear el ícono del systray con el menú
        self.icon = Icon("Imputaciones", icon_image, self.tooltip_text, menu)
        self.initialized.set()  # Marcar como inicializado
        self.icon.run()

    def toggle_app_window(self, icon=None, item=None):
        """Alterna entre mostrar y ocultar la ventana principal de la aplicación."""
        if not self.app.root.winfo_viewable():  # Si la ventana no es visible
            self.app.root.deiconify()  # Mostrar la ventana
        else:
            self.app.root.withdraw()  # Ocultar la ventana

    def update_tooltip(self, new_text):
        """Actualiza el texto del tooltip del systray y el menú de información."""
        if self.icon:
            self.icon.title = new_text

    def quit_application(self):
        """Cierra la aplicación desde el systray."""
        if self.icon:
            self.icon.stop()  # Detiene el systray
        self.app.quit_application()  # Llama al método de la aplicación para cerrar

    def update_menu_items(self, updates):
        """
        Actualiza las propiedades de uno o más ítems del menú.
        :param updates: Diccionario donde las claves son los nombres de los ítems
                        y los valores son diccionarios con las propiedades a actualizar.
        """
        menu_updated = False

        for item_name, kwargs in updates.items():
            if item_name in self.menu_items:
                # Recuperar la acción existente desde `menu_actions`
                action = self.menu_actions.get(item_name, None)

                # Crear un nuevo `MenuItem` con las propiedades actualizadas
                current_item = self.menu_items[item_name]
                new_text = kwargs.get("text", current_item.text)
                new_default = kwargs.get("default", current_item.default)
                new_visible = kwargs.get("visible", current_item.visible)
                new_enabled = kwargs.get("enabled", current_item.enabled)

                updated_item = MenuItem(
                    new_text,
                    action,  # Usar la acción asociada previamente
                    default=new_default,
                    visible=new_visible,
                    enabled=new_enabled,
                )

                if updated_item != current_item:
                    self.menu_items[item_name] = updated_item
                    menu_updated = True

        if menu_updated and self.icon:
            new_menu = Menu(*self.menu_items.values())
            self.icon.menu = new_menu
            self.icon.update_menu()
