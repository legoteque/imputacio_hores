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
        self.filas_no_interactivas = set()  # ⭐ NUEVO: Conjunto de IDs no interactivos

        # Definir columnas con sus nombres adecuados (ahora "checkbox" es el primer elemento)
        self.tree = ttk.Treeview(self.frame, columns=COLUMNAS_TREE, show="headings", height=10)
        self._configurar_treeview()


    def _configurar_treeview(self):
        """
        Configura el Treeview con las columnas y encabezados.
        """     
        # Estado de ordenamiento (inicialmente vacío)
        self.orden_actual = {col: False for col in ("tiempo","empresa","concepto","fecha_creacion")}

        # Encabezados de las columnas visibles con evento de ordenación
        self.tree.heading("checkbox", text="✓", command=self.toggle_all_checkboxes)
        self.tree.heading("fecha_creacion", text="Fecha", command=lambda: self.ordenar_treeview("fecha_creacion"))
        self.tree.heading("empresa", text="Empresa", command=lambda: self.ordenar_treeview("empresa"))
        self.tree.heading("concepto", text="Concepto", command=lambda: self.ordenar_treeview("concepto"))
        self.tree.heading("tiempo", text="Tiempo", command=lambda: self.ordenar_treeview("tiempo"))

        # Configuración de columnas visibles
        self.tree.column("checkbox", width=20, minwidth=20, anchor="center", stretch=False)
        self.tree.column("fecha_creacion", width=100, minwidth=100, anchor="center", stretch=False)
        self.tree.column("empresa", width=200, minwidth=150, anchor="center", stretch=True)
        self.tree.column("concepto", width=200, minwidth=150, anchor="center", stretch=True)
        self.tree.column("tiempo", width=80, minwidth=80, anchor="center", stretch=False)


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

    def agregar_fila(self, registro_id, tiempo_formateado, empresa, concepto, fecha_formateada, 
                tiempo_original, fecha_original, es_interactivo=True):
        """
        Agrega una fila al Treeview con checkbox apropiado según interactividad.
        """
        checkbox_estado = " " if not es_interactivo else " "  
        
        # ✅ ORDEN CORRECTO - fecha primero, tiempo después (según títulos)
        self.tree.insert("", "end", iid=str(registro_id), 
                        values=(checkbox_estado, fecha_formateada, empresa, concepto, tiempo_formateado, tiempo_original, fecha_original))

        
        # ⭐ CONFIGURAR ESTILO SEGÚN INTERACTIVIDAD
        if not es_interactivo:
            self.filas_no_interactivas.add(str(registro_id))
            self.tree.item(str(registro_id), tags=("no_interactivo",))
            self.tree.tag_configure("no_interactivo", background="#f0f0f0", foreground="#888888")

    def actualizar_fila(self, registro_id, tiempo_formateado, empresa, concepto, fecha_formateada, tiempo_original, fecha_original):
        """
        Actualiza una fila en el Treeview manteniendo su estado de interactividad.
        """
        # ✅ ORDEN CORRECTO - fecha primero, tiempo después
        self.tree.item(str(registro_id), values=(" ", fecha_formateada, empresa, concepto, tiempo_formateado, tiempo_original, fecha_original))

        
        # ⭐ RESTAURAR ESTILO SI ES NO INTERACTIVA
        if str(registro_id) in self.filas_no_interactivas:
            self.tree.item(str(registro_id), tags=("no_interactivo",))
            self.tree.tag_configure("no_interactivo", background="#f0f0f0", foreground="#888888")


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
        """Limpia el TreeView y reinicia el conjunto de filas no interactivas."""
        self.tree.delete(*self.tree.get_children())
        self.filas_no_interactivas.clear()  # ⭐ LIMPIAR CONJUNTO

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
        Actualizar el estado de cada checkbox SOLO en las filas interactivas.
        Las filas no interactivas NUNCA cambian su estado de checkbox.
        """
        for item in self.tree.get_children():
            # ⭐ SOLO MODIFICAR SI LA FILA ES INTERACTIVA
            if item not in self.filas_no_interactivas:
                valores = self.tree.item(item, "values")
                nuevos_valores = (nuevo_estado,) + valores[1:]  # Modificar solo la primera columna
                self.tree.item(item, values=nuevos_valores)

        # Verificar si hay checkboxes seleccionados
        self.actualizar_estado_frame()
    
    def toggle_all_checkboxes(self):
        """
        Marca o desmarca todos los checkboxes SOLO en las filas interactivas.
        Las filas no interactivas nunca se ven afectadas.
        """
        # ⭐ VERIFICAR SOLO LAS FILAS INTERACTIVAS PARA DETERMINAR EL ESTADO
        filas_interactivas = [item for item in self.tree.get_children() if item not in self.filas_no_interactivas]
        
        if not filas_interactivas:
            return  # Si no hay filas interactivas, no hacer nada
        
        # Verificar si todas las filas INTERACTIVAS están marcadas
        todos_seleccionados = all(
            self.tree.item(item, "values")[0] == "✔" 
            for item in filas_interactivas
        )

        # Determinar el nuevo estado a aplicar (solo a filas interactivas)
        nuevo_estado = " " if todos_seleccionados else "✔"

        # ⭐ APLICAR SOLO A FILAS INTERACTIVAS
        self.set_all_checkboxes(nuevo_estado)


    def toggle_single_checkbox(self, item):
        """
        Solo permite toggle de checkbox en filas interactivas.
        """
        if item in self.filas_no_interactivas:
            return  # No hacer nada si la fila no es interactiva
        
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
        Muestra u oculta el frame inferior si hay algún checkbox marcado EN FILAS INTERACTIVAS.
        Solo considera las filas interactivas para determinar si mostrar botones.
        """
        # ⭐ VERIFICAR SOLO CHECKBOXES DE FILAS INTERACTIVAS
        hay_seleccionados = any(
            self.tree.item(item, "values")[0] == "✔" 
            for item in self.tree.get_children() 
            if item not in self.filas_no_interactivas  # Solo filas interactivas
        )
        
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
        Ignora clics en filas no interactivas.
        """
        self.deseleccionar_fila()  # Siempre ejecuta esto

        if not self.interaccion_treeview:
            return  # Si está deshabilitado, no hace nada más

        try:
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if not item:
                return  # Si no se identifica una fila, no hacer nada

            # ⭐ VERIFICAR SI LA FILA ES NO INTERACTIVA
            if item in self.filas_no_interactivas:
                return  # No hacer nada si la fila no es interactiva

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
            pass



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
        Muestra el menú contextual solo para filas interactivas.
        """
        if not self.interaccion_treeview:
            return

        # Identificar la fila bajo el cursor
        item = self.tree.identify_row(event.y)
        if item and item not in self.filas_no_interactivas:  # ⭐ VERIFICAR INTERACTIVIDAD
            self.set_all_checkboxes(nuevo_estado=" ")
            self.seleccionado = item
            self.tree.selection_set(item)
            valores = self.tree.item(item)["values"]
            if valores:
                self.menu_contextual.entryconfigure(0, label=valores[2])
                self.menu_contextual.post(event.x_root, event.y_root)
        else:
            self.seleccionado = None


    def color_fila(self, color="white", id_fila=None):
        """
        Cambia el color de una fila específica en el Treeview o restablece todas las filas a blanco.
        RESPETA siempre el estilo de las filas no interactivas.
        """
        children = self.tree.get_children()

        if not children:
            return  # Si no hay filas, salir

        id_fila = str(id_fila)  # Convertir a str para asegurar coincidencia con get_children()

        if color == "white":
            # Restablecer todas las filas a fondo blanco, EXCEPTO las no interactivas
            for fila in children:
                if fila not in self.filas_no_interactivas:  # ⭐ PROTEGER FILAS NO INTERACTIVAS
                    self.tree.item(fila, tags=("default",))
                # ⭐ NO TOCAR las filas no interactivas, mantienen su estilo gris
            self.tree.tag_configure("default", background="white", foreground="black")
        
        elif id_fila is not None:
            # ⭐ SOLO APLICAR COLOR SI LA FILA ES INTERACTIVA
            if id_fila in children and id_fila not in self.filas_no_interactivas:
                if color == "green":
                    self.tree.item(id_fila, tags=("highlighted_green",))
                    self.tree.tag_configure("highlighted_green", background="green", foreground="white")
                else:
                    self.tree.item(id_fila, tags=("highlighted",))
                    self.tree.tag_configure("highlighted", background=color, foreground="black")
        
        # ⭐ RECONFIGURAR SIEMPRE EL ESTILO NO INTERACTIVO PARA ASEGURAR QUE SE MANTIENE
        self.tree.tag_configure("no_interactivo", background="#f0f0f0", foreground="#888888")