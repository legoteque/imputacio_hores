import tkinter as tk
from tkinter import ttk, Menu
from datetime import datetime
from functions import COLORES, COLUMNAS_TREE

class TreeviewManager:
    def __init__(self, register):
        self.register = register
        self.frame = register.frame

        self.interaccion_treeview = True # Variable para controlar si el menú contextual y la posiblidad de seleccionar un registro está habilitada
        self.seleccionado = None  # Variable para mantener el registro seleccionado

        # Definir columnas con sus nombres adecuados (ahora "checkbox" es el primer elemento)
        self.tree = ttk.Treeview(self.frame, columns=COLUMNAS_TREE, show="headings", height=10)
        self._configurar_treeview()
        
        self.tree.bind("<Button-1>", self.click_izquierdo)  # Asocia el evento para capturar click izquierdo sobre el treeview


    def _configurar_treeview(self):
        """
        Configura el Treeview con las columnas y encabezados.
        """     
        # Estado de ordenamiento (inicialmente vacío)
        self.orden_actual = {col: False for col in ("tiempo","empresa","concepto","fecha_creacion")}

        # Encabezados de las columnas visibles con evento de ordenación
        self.tree.heading("checkbox", text="✓", command=self.toggle_all_checkboxes)
        self.tree.heading("tiempo", text="Tiempo", command=lambda: self.ordenar_treeview("tiempo"))
        self.tree.heading("empresa", text="Empresa", command=lambda: self.ordenar_treeview("empresa"))
        self.tree.heading("concepto", text="Concepto", command=lambda: self.ordenar_treeview("concepto"))
        self.tree.heading("fecha_creacion", text="Fecha", command=lambda: self.ordenar_treeview("fecha_creacion"))

        # Configuración de columnas visibles con ancho mínimo y stretch=False
        self.tree.column("checkbox", width=20, minwidth=20, anchor="center", stretch=False)
        self.tree.column("tiempo", width=80, minwidth=80, anchor="center", stretch=False)
        self.tree.column("empresa", width=150, minwidth=150, anchor="center", stretch=True)
        self.tree.column("concepto", width=150, minwidth=150, anchor="center", stretch=False)
        self.tree.column("fecha_creacion", width=100, minwidth=100, anchor="center", stretch=False)

        # Configuración de columnas ocultas (tiempo y fecha originales)
        self.tree.column("time", width=0, stretch=False)  # Oculta la columna original del tiempo
        self.tree.column("date", width=0, stretch=False)  # Oculta la columna original de la fecha

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollbar horizontal
        scrollbar_x = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscroll=scrollbar_x.set)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Empaquetar la tabla
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Evento de clic derecho (menú contextual)
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)

        # Crear el menú contextual
        self.menu_contextual = Menu(self.frame, tearoff=0)
        self.menu_empresa = self.menu_contextual.add_command(label="", state=tk.DISABLED)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Editar", command=self.register.editar)
        self.menu_contextual.add_command(label="Borrar", command=lambda: self.register.borrar(desde_menu=True))
        self.menu_contextual.add_command(label="Imputar", command=lambda: self.register.imputar(desde_menu=True))

        #Evento de clic izquierdo
        self.tree.bind("<Button-1>", self.click_izquierdo)

        self.bottom_frame = tk.Frame(self.frame, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")

        # Crear botones con los estilos personalizados
        delete_button = ttk.Button(self.bottom_frame, text="🗑 Borrar", command=self.register.borrar)
        delete_button.pack(side=tk.LEFT, padx=10, pady=10)

        imputar_button = ttk.Button(self.bottom_frame, text="✅ Imputar", command=self.register.imputar)
        imputar_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Inicialmente ocultar el frame
        self.bottom_frame.pack_forget()

    def agregar_fila(self, registro_id, tiempo_formateado, empresa, concepto, fecha_formateada, tiempo_original, fecha_original):
        """
        Agrega una fila al Treeview.
        """
        self.tree.insert("", 0, iid=str(registro_id), values=(" ", tiempo_formateado, empresa, concepto, fecha_formateada, tiempo_original, fecha_original))

    def actualizar_fila(self, registro_id, tiempo_formateado, empresa, concepto, fecha_formateada, tiempo_original, fecha_original):
        """
        Actualiza una fila en el Treeview.
        """
        self.tree.item(str(registro_id), values=(" ", tiempo_formateado, empresa, concepto, fecha_formateada, tiempo_original, fecha_original))

    def borrar_fila(self, registro_id):
        """
        Borra una fila del Treeview.
        """
        self.tree.delete(registro_id)

    def deseleccionar_fila(self):
        """
        Fuerza la deselección de cualquier fila seleccionada en el Treeview después de un pequeño retardo.
        Esto evita que queden resaltadas en gris.
        """
        self.tree.after(10, lambda: self.tree.selection_remove(self.tree.selection()))

    def limpiar_tree(self):
        self.tree.delete(*self.tree.get_children())

    def ordenar_treeview(self, columna):
        """
        Ordena el Treeview por la columna seleccionada alternando entre ascendente y descendente.
        Maneja tiempos como enteros y fechas como objetos datetime para ordenarlos correctamente.
        """
        # Determinar la columna de ordenación real
        if columna == "tiempo":
            columna_orden = "time"  # Ordenar por la columna oculta 'time'
        elif columna == "fecha_creacion":
            columna_orden = "date"  # Ordenar por la columna oculta 'date'
        else:
            columna_orden = columna  # Ordenar por la columna visible directamente

        for item in self.tree.get_children(""):
            valor = self.tree.set(item, columna_orden)
            print(f"Item: {item}, Valor en columna '{columna_orden}': {valor}")

        # Obtener todos los elementos del Treeview
        items = []
        for item in self.tree.get_children(""):
            valor = self.tree.set(item, columna_orden)  # Obtener el valor de la columna de ordenación
            if columna_orden == "time":
                valor = int(valor)  # Convertir tiempos a enteros
            elif columna_orden == "date":
                try:
                    valor = datetime.strptime(valor, "%Y-%m-%d %H:%M")  # Convertir fechas a objetos datetime
                except ValueError:
                    valor = None  # Manejar valores inválidos
            items.append((valor, item))

        # Determinar el orden (alternar entre ascendente y descendente)
        if self.orden_actual[columna]:
            items.sort(reverse=True, key=lambda x: x[0])  # Orden descendente
            self.orden_actual[columna] = False
        else:
            items.sort(key=lambda x: x[0])  # Orden ascendente
            self.orden_actual[columna] = True

        # Reorganizar los elementos en el Treeview
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

        # Actualizar el estado de ordenamiento
        self.actualizar_encabezados(columna)


    def set_all_checkboxes(self, nuevo_estado="✔"):
        """
        Actualizar el estado de cada checkbox en la última columna
        """
        for item in self.tree.get_children():
            valores = self.tree.item(item, "values")
            nuevos_valores = (nuevo_estado,) + valores[1:]  # Modificar solo la primera columna
            self.tree.item(item, values=nuevos_valores)

        # Verificar si hay checkboxes seleccionados
        self.actualizar_estado_frame()
    
    def toggle_all_checkboxes(self):
        """
        Marca o desmarca todos los checkboxes en el Treeview.
        """
        # Verificar si todos los checkboxes están marcados (última columna)
        todos_seleccionados = all(self.tree.item(item, "values")[0] == "✔" for item in self.tree.get_children())

        print("todos seleccionados?", todos_seleccionados)

        # Determinar el nuevo estado a aplicar
        nuevo_estado = " " if todos_seleccionados else "✔"

        self.set_all_checkboxes(nuevo_estado)

    def toggle_single_checkbox(self, item):
        """
        Alterna el estado de un solo checkbox en el Treeview.
        """
        valores = self.tree.item(item, "values")
        checkbox_state = valores[0]  # Primera columna

        # Alternar entre "✔" y " "
        nuevo_estado = "✔" if checkbox_state == " " else " "

        # Actualizar solo la columna del checkbox
        nuevos_valores = (nuevo_estado,) + valores[1:]
        self.tree.item(item, values=nuevos_valores)

        # Verificar si hay checkboxes seleccionados
        self.actualizar_estado_frame()


    def actualizar_estado_frame(self):
        """
        Muestra u oculta el frame inferior si hay algun checkbox seleccionado.
        """
        # Verificar si hay al menos un checkbox marcado
        hay_seleccionados = any(self.tree.item(item, "values")[0] == "✔" for item in self.tree.get_children())
        
        if hay_seleccionados:
            # Mostrar el frame si no está visible
            if not self.bottom_frame.winfo_ismapped():
                self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        else:
            # Ocultar el frame si no hay checkboxes seleccionados
            if self.bottom_frame.winfo_ismapped():
                self.bottom_frame.pack_forget()

    def actualizar_encabezados(self, columna_ordenada):
        """
        Actualiza los encabezados del Treeview para mostrar una flecha que indica el orden actual.
        """
        for col in self.orden_actual:
            # Obtener el texto actual del encabezado
            texto_actual = self.tree.heading(col, "text")
            if col == columna_ordenada:
                # Agregar el símbolo según el orden
                if self.orden_actual[col]:
                    self.tree.heading(col, text=f"{texto_actual.split(' ')[0]} ▲")
                else:
                    self.tree.heading(col, text=f"{texto_actual.split(' ')[0]} ▼")
            else:
                # Restaurar el texto original sin el símbolo
                self.tree.heading(col, text=texto_actual.split(' ')[0])

    def click_izquierdo(self, event):
        """
        Maneja el clic izquierdo en el Treeview.
        Siempre deselecciona filas, pero el resto del proceso depende de si está habilitado o no.
        """
        print("click izquierdo")
        self.deseleccionar_fila()  # Siempre ejecuta esto

        if not self.interaccion_treeview:
            return  # Si está deshabilitado, no hace nada más

        try:
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            # Depuración: Mostrar información del clic
            print(f"Clic izquierdo: región={region}, columna={column}, fila={item}")

            if not item:
                return  # Si no se identifica una fila, no hacer nada

            # Si el clic es en el encabezado de la columna checkbox
            if region == "heading":              
                return

            # Si el clic es en una celda de la columna checkbox
            if region == "cell" and column == "#1":
                self.toggle_single_checkbox(item)
                return

            # Si el clic es en otra celda de la fila
            if region == "cell":
                self.register.recuperar(item)

        except Exception as e:
            print(f"Error al manejar el clic izquierdo: {e}")




    def habilitar_interaccion_treeview(self, habilitar=True):
        """
        Habilita o deshabilita el menú contextual y la posiblidad de seleccionar un registro.
        """
        self.interaccion_treeview = habilitar
        if habilitar:
            self.tree.bind("<Button-3>", self.mostrar_menu_contextual)
        else:
            self.tree.unbind("<Button-3>")  # Desvincula el evento del clic derecho

    def mostrar_menu_contextual(self, event):
        """
        Muestra el menú contextual al hacer clic derecho sobre una fila solo si está habilitado.
        Selecciona automáticamente la fila clicada.
        """

        if not self.interaccion_treeview:
            return  # No hacer nada si el menú está deshabilitado
        
        self.set_all_checkboxes(nuevo_estado=" ")

        # Identificar la fila bajo el cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.seleccionado = item
            # Seleccionar visualmente la fila
            self.tree.selection_set(item)
            valores = self.tree.item(item)["values"]
            # Asegurarse de que hay valores antes de configurar el menú
            if valores:
                # Actualizar la etiqueta del menú contextual para mostrar solo el nombre de la empresa
                self.menu_contextual.entryconfigure(0, label=valores[2])
                self.menu_contextual.post(event.x_root, event.y_root)
            else:
                print(f"No hay valores en la fila {item}.")
                self.seleccionado = None
        else:
            self.seleccionado = None


    def color_fila(self, color="white", id_fila=None):
        """
        Cambia el color de una fila específica en el Treeview o restablece todas las filas a blanco.

        Parámetros:
            color (str): Color a aplicar ("green", "white", etc.). Por defecto es "white".
            id_fila (int/str): ID de la fila a la que se aplicará el color. Si es None, se restablecen todas las filas.
        """
        children = self.tree.get_children()

        if not children:
            return  # Si no hay filas, salir

        id_fila = str(id_fila)  # Convertir a str para asegurar coincidencia con get_children()

        if color == "white":
            # Restablecer todas las filas a fondo blanco y texto negro
            for fila in children:
                self.tree.item(fila, tags=("default",))  # Elimina los tags para restaurar el color original
            self.tree.tag_configure("default", background="white", foreground="black")
        
        elif id_fila is not None:
            # Aplicar el color a la fila específica
            if id_fila in children:  # Verificar que el ID exista en el Treeview
                if color == "green":
                    self.tree.item(id_fila, tags=("highlighted_green",))
                    self.tree.tag_configure("highlighted_green", background="green", foreground="white")
                else:
                    self.tree.item(id_fila, tags=("highlighted",))
                    self.tree.tag_configure("highlighted", background=color, foreground="black")
            else:
                print(f"ID de fila {id_fila} no encontrado en el Treeview.")
        else:
            print("Se requiere un ID de fila para aplicar un color específico.")
