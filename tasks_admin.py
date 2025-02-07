import sqlite3, json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, Menu
#import styles
from functions import formatear_fecha, return_fecha_actual, seconds_to_string
from functions import COLORES

db_path = r"data/treeview_data.db"

class TasksAdmin:
    def __init__(self, root, app, manager):
        self.app = app
        self.manager = manager

        self.menu_habilitado = True  # Variable para controlar si el menú está habilitado
        self.seleccionado = None  # Variable para mantener el registro seleccionado

        # Conectar a SQLite
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        self._crear_tabla()

        # Frame principal para la tabla y el scrollbar
        self.frame = ttk.Frame(root)
        
        # Definir columnas con sus nombres adecuados (ahora "checkbox" es el primer elemento)
        self.tree = ttk.Treeview(self.frame, columns=("checkbox", "formatted_time", "empresa", "concepto", "formatted_date", "time", "date"),
                                show="headings", height=10)

        # Estado de ordenamiento (inicialmente vacío)
        self.orden_actual = {col: False for col in ("checkbox","formatted_time","empresa","concepto","formatted_date")}

        # Encabezados de las columnas visibles con evento de ordenación
        self.tree.heading("checkbox", text="✓", command=self.toggle_all_checkboxes)
        self.tree.heading("formatted_time", text="Tiempo", command=lambda: self.ordenar_treeview("formatted_time"))
        self.tree.heading("empresa", text="Empresa", command=lambda: self.ordenar_treeview("empresa"))
        self.tree.heading("concepto", text="Concepto", command=lambda: self.ordenar_treeview("concepto"))
        self.tree.heading("formatted_date", text="Fecha", command=lambda: self.ordenar_treeview("formatted_date"))

        
        # Configuración de columnas visibles con ancho mínimo y stretch=False
        self.tree.column("checkbox", width=20, minwidth=20, anchor="center", stretch=False)
        self.tree.column("formatted_time", width=80, minwidth=80, anchor="center", stretch=False)
        self.tree.column("empresa", width=150, minwidth=150, anchor="center", stretch=True)
        self.tree.column("concepto", width=150, minwidth=150, anchor="center", stretch=False)
        self.tree.column("formatted_date", width=100, minwidth=100, anchor="center", stretch=False)

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
        self.menu_contextual = Menu(root, tearoff=0)
        self.menu_empresa = self.menu_contextual.add_command(label="", state=tk.DISABLED)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Editar", command=self.editar)
        self.menu_contextual.add_command(label="Borrar", command=lambda: self.borrar(desde_menu=True))
        self.menu_contextual.add_command(label="Imputar", command=lambda: self.imputar(desde_menu=True))

        #Evento de clic izquierdo
        self.tree.bind("<Button-1>", self.click_izquierdo)

        self.bottom_frame = tk.Frame(self.frame, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")

        # Crear botones con los estilos personalizados
        delete_button = ttk.Button(self.bottom_frame, text="🗑 Borrar", command=self.borrar, style="Borrar.TButton")
        delete_button.pack(side=tk.LEFT, padx=10, pady=10)

        imputar_button = ttk.Button(self.bottom_frame, text="✅ Imputar", command=self.imputar, style="Imputar.TButton")
        imputar_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Inicialmente ocultar el frame
        self.bottom_frame.pack_forget()

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

    
    def set_all_checkboxes(self, nuevo_estado="✔"):
        # Actualizar el estado de cada checkbox en la última columna
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


    def click_izquierdo(self, event):
        """
        Maneja el clic izquierdo en el Treeview.
        """
        try:
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            # Depuración: Mostrar información del clic
            print(f"Clic izquierdo: región={region}, columna={column}, fila={item}")

            if not item:
                print("No se identificó una fila. Ignorando el clic.")
                return  # Si no se identifica una fila, no hacer nada

            # Si el clic es en el encabezado de la columna checkbox
            if region == "heading":              
                return

            # Si el clic es en una celda de la columna checkbox
            if region == "cell" and column == "#1":
                print(f"Clic en checkbox de la fila {item}.")
                self.toggle_single_checkbox(item)
                return

            # Si el clic es en otra celda de la fila
            if region == "cell":
                print(f"Clic en la fila {item}. Llamando a recuperar.")
                self.recuperar(item)

        except Exception as e:
            print(f"Error al manejar el clic izquierdo: {e}")


    def recuperar(self, item):
        """
        Recupera información de la fila seleccionada y maneja errores.
        """
        if not item:
            print("Error: Se intentó recuperar un ítem inválido.")
            return

        try:
            # Recuperar datos del registro de la base de datos
            registro_id = str(item)
            register_dic = self.get_db_register(registro_id)

            if register_dic != None:
                # Recuperar datos del registro
                self.app.restored_task(register_dic["id"], register_dic["tiempo"], register_dic["empresa"], register_dic["concepto"])
            else:
                print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
                return

            # Forzar la deselección después del clic (evita el gris)
            self.tree.after(10, lambda: self.tree.selection_remove(self.tree.selection()))

        except Exception as e:
            print(f"Error al recuperar información de la fila {item}: {e}")


    

    def ordenar_treeview(self, columna):
        """
        Ordena el Treeview por la columna seleccionada alternando entre ascendente y descendente.
        Maneja tiempos como enteros y fechas como objetos datetime para ordenarlos correctamente.
        """
        #for item in self.tree.get_children(""):
            # valor = self.tree.set(item, "date")
            # print(f"Valor para {item}: {valor}")  # Depurar los valores

        # Determinar la columna de ordenación real
        if columna == "formatted_time":
            columna_orden = "time"  # Ordenar por la columna oculta 'time'
        elif columna == "formatted_date":
            columna_orden = "date"  # Ordenar por la columna oculta 'date'
        else:
            columna_orden = columna  # Ordenar por la columna visible directamente

        # Obtener todos los elementos del Treeview
        items = []
        for item in self.tree.get_children(""):
            valor = self.tree.set(item, columna_orden)  # Obtener el valor de la columna de ordenación
            if columna_orden == "time":
                valor = int(valor)  # Convertir tiempos a enteros
            elif columna_orden == "date":
                try:
                    valor = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")  # Convertir fechas a objetos datetime
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


    def habilitar_clic_izquierdo(self, habilitar=True):
        """
        Habilita o deshabilita los eventos del clic izquierdo en el Treeview.
        """
        if habilitar:
            self.tree.bind("<Button-1>", self.click_izquierdo) # Vuelve a asociar el evento
        else:
            self.tree.unbind("<Button-1>")  # Desvincula el evento del clic izquierdo


    def habilitar_menu_contextual(self, habilitar=True):
        """
        Habilita o deshabilita el menú contextual.
        """
        self.menu_habilitado = habilitar
        if habilitar:
            self.tree.bind("<Button-3>", self.mostrar_menu_contextual)
        else:
            self.tree.unbind("<Button-3>")  # Desvincula el evento del clic derecho

    def mostrar_menu_contextual(self, event):
        """
        Muestra el menú contextual al hacer clic derecho sobre una fila solo si está habilitado.
        Selecciona automáticamente la fila clicada.
        """

        if not self.menu_habilitado:
            return  # No hacer nada si el menú está deshabilitado

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
                self.menu_contextual.entryconfigure(0, label=valores[1])
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


    def _crear_tabla(self):
        """
        Crea la tabla en SQLite si no existe.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tiempo TEXT,
                empresa TEXT,
                concepto TEXT,
                fecha_creacion TEXT,
                fecha_imputacion TEXT,
                state TEXT,
                user TEXT,
                departamento TEXT
            )
        """)
        self.conexion.commit()




    def cargar_datos_desde_sqlite(self):
        """
        Carga los registros existentes desde SQLite al Treeview filtrados por usuario.
        """
        self.tree.delete(*self.tree.get_children())  # Limpia el Treeview antes de cargar nuevos datos
        self.cursor.execute("""
            SELECT id, tiempo, empresa, concepto, fecha_creacion
            FROM registros 
            WHERE state = 'working' AND user = ?
        """, (self.manager.user,))
        
        for row in self.cursor.fetchall():
            # Datos originales
            tiempo_original = int(row[1])  # Tiempo en segundos
            fecha_original = row[4]   # Fecha en formato YYYY-MM-DD HH:MM:SS

            # Convertir los datos al formato visual para la UI
            tiempo_formateado = seconds_to_string(tiempo_original, include_seconds=False)
            fecha_formateada = formatear_fecha(fecha_original)

            # Insertar en el Treeview con columnas visibles y ocultas
            self.tree.insert("", "end", iid=str(row[0]),
                values=(" ", tiempo_formateado, row[2], row[3], fecha_formateada, tiempo_original, fecha_original))



    def agregar_fila(self, time, empresa, concepto):
        """
        Agrega una fila nueva al Treeview (arriba) y a SQLite en cuanto iniciamos el concepto.
        """
        # Fecha actual
        fecha_actual = return_fecha_actual()

        # Insertar en SQLite
        self.cursor.execute("""
            INSERT INTO registros (tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, state, user, departamento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (time, empresa, concepto, fecha_actual, None, "working", self.manager.user, self.manager.department))
        self.conexion.commit()
        row_id = self.cursor.lastrowid  # Obtener el id generado por SQLite

        # Convertir los datos al formato visual
        fecha_formateada = formatear_fecha(fecha_actual)  # Convertir la fecha al formato DD/MM/AA
        tiempo_formateado = seconds_to_string(time, include_seconds=False)  # Convertir tiempo a formato legible

        # Insertar en el Treeview con columnas visibles y ocultas
        self.tree.insert(
            "", 0, iid=str(row_id),
            values=(" ",tiempo_formateado, empresa, concepto, fecha_formateada, int(time), fecha_actual))

        return row_id



    def time_update(self, id_registro, time):
        """
        Actualiza el campo 'tiempo' del registro identificado por su ID en el Treeview
        y lo sincroniza con la base de datos.

        Parámetros:
            id_registro (str/int): ID del registro a actualizar (mismo en Treeview y DB).
            time (str/int): Nuevo valor para el campo 'tiempo'.
        """
        print("entra a time_update")

        # Convertir id_registro a str para coincidir con el iid del Treeview
        id_registro = str(id_registro)

        # Verificar si el registro está en el Treeview
        if id_registro not in self.tree.get_children():
            print(f"ID {id_registro} no encontrado en el Treeview.")
            return

        # Obtener los valores actuales de la fila en el Treeview
        valores_actuales = self.tree.item(id_registro)["values"]
        empresa_actual = valores_actuales[2]  # Mantener el valor de 'empresa'
        concepto_actual = valores_actuales[3]  # Mantener el valor de 'concepto'
        fecha_formateada = valores_actuales[4]  # Mantener el valor de 'fecha'
        date = valores_actuales[5]

        # Actualizar la base de datos
        self.cursor.execute("""
            UPDATE registros
            SET tiempo = ?
            WHERE id = ?
        """, (time, id_registro))
        self.conexion.commit()

        # Convertir el tiempo a formato legible antes de actualizar el Treeview
        tiempo_formateado = seconds_to_string(time, include_seconds=False)

        # Actualizar el Treeview con los nuevos valores
        nuevos_valores = (" ", tiempo_formateado, empresa_actual, concepto_actual, fecha_formateada, time, date)
        self.tree.item(id_registro, values=nuevos_valores)


    def pack_forget(self):
        """
        Oculta el Treeview y su contenedor.
        """
        self.frame.pack_forget()  # Oculta el frame completo

    def pack(self):
        """
        Muestra el Treeview y su contenedor.
        """
        self.frame.pack(fill=tk.BOTH, expand=True)  # Muestra el frame completo


    def get_db_register(self, registro_id):
        """
        Obtiene un registro de la base de datos por su ID y devuelve un diccionario con columna: valor.
        """
        self.cursor.execute("""
            SELECT id, tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, state, user, departamento
            FROM registros
            WHERE id = ?
        """, (registro_id,))
        registro = self.cursor.fetchone()
        
        if not registro:
            return None
    
        columnas = ["id", "tiempo", "empresa", "concepto", "fecha_creacion", "fecha_imputacion", "state", "user", "departamento"]
        return dict(zip(columnas, registro))


    def editar(self):
        """
        Muestra un popup para editar un registro seleccionado.
        """
        if not self.seleccionado:
            print("No hay un registro seleccionado para editar.")
            return

        # Obtener el id (iid del Treeview)
        registro_id = int(self.seleccionado)

        registro_dic = self.get_db_register(registro_id)

        if registro_dic is None:
            print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
            return

        # Crear ventana emergente
        popup = tk.Toplevel()
        popup.title("Editar Registro")
        popup.geometry("400x400")

        entries = {}
        labels = [
            "Tiempo (segundos):", "Empresa:", "Concepto:", "Fecha Creación:", 
            "Fecha Imputación:", "Estado:", "Usuario:", "Departamento:"
        ]
        campos = ["tiempo", "empresa", "concepto", "fecha_creacion", 
                "fecha_imputacion", "state", "user", "departamento"]

        for i, label_text in enumerate(labels):
            tk.Label(popup, text=label_text).pack()
            entry = tk.Entry(popup)
            
            # Convertir valores a cadenas y manejar None
            value = str(registro_dic.get(campos[i], "") or "")
            entry.insert(0, value)
            entry.pack()
            entries[campos[i]] = entry

        def guardar_cambios():
            """ Guarda los cambios en la base de datos y en el Treeview """
            nuevos_valores = {campo: entry.get() for campo, entry in entries.items()}

            # Actualizar en la base de datos
            self.cursor.execute("""
                UPDATE registros
                SET tiempo = ?, empresa = ?, concepto = ?, fecha_creacion = ?, 
                    fecha_imputacion = ?, state = ?, user = ?, departamento = ?
                WHERE id = ?
            """, (
                nuevos_valores["tiempo"], nuevos_valores["empresa"], nuevos_valores["concepto"], 
                nuevos_valores["fecha_creacion"], nuevos_valores["fecha_imputacion"], 
                nuevos_valores["state"], nuevos_valores["user"], nuevos_valores["departamento"], 
                registro_id
            ))
            self.conexion.commit()

            # Actualizar en el Treeview solo los valores visibles
            tiempo_formateado = seconds_to_string(int(nuevos_valores["tiempo"]), include_seconds=False)
            fecha_formateada = formatear_fecha(nuevos_valores["fecha_creacion"])
            self.tree.item(self.seleccionado, values=(
                " ", tiempo_formateado, nuevos_valores["empresa"], nuevos_valores["concepto"],
                fecha_formateada, nuevos_valores["tiempo"]
            ))

            popup.destroy()

        # Botón para guardar cambios
        btn_guardar = tk.Button(popup, text="Guardar", command=guardar_cambios)
        btn_guardar.pack(pady=10)




    def borrar(self, desde_menu=False):
        """
        Borra una fila seleccionada si se llama desde el menú contextual.
        Si se llama desde el botón de borrar, borra todas las filas con checkbox marcado.
        """
        print("entra a borrar")
        if desde_menu:
            # Borrar solo el elemento seleccionado del menú contextual
            if self.seleccionado:
                # self.cursor.execute("DELETE FROM registros WHERE id = ?", (self.seleccionado,))
                # self.conexion.commit()º
                # self.tree.delete(self.seleccionado)
                # self.seleccionado = None
                print("borrado desde el menú contextual:", self.seleccionado)
        else:
            # Borrar todos los elementos con checkbox marcado
            items_a_borrar = [item for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "✔"]

            if items_a_borrar:
                # self.cursor.executemany("DELETE FROM registros WHERE id = ?", [(item,) for item in items_a_borrar])
                # self.conexion.commit()
                # for item in items_a_borrar:
                #     self.tree.delete(item)
                print("borrados desde checkbox los items: ", items_a_borrar)

    def imputar(self, desde_menu=False):
        """
        Imputa un registro cambiando su estado a 'imputado'.
        - Si se llama desde el menú contextual, solo imputa la fila seleccionada.
        - Si se llama desde el botón inferior, imputa todas las filas con checkbox marcado.
        """
        fecha_actual = return_fecha_actual()
        print("entra a imputar")
        if desde_menu:
            # Imputar solo el elemento seleccionado del menú contextual
            if self.seleccionado:
                # self.cursor.execute("""
                #     UPDATE registros
                #     SET state = 'imputado', fecha_imputacion = ?
                #     WHERE id = ?
                # """, (fecha_actual, self.seleccionado))
                # self.conexion.commit()
                # # Eliminar del Treeview
                # self.tree.delete(self.seleccionado)
                # self.seleccionado = None
                print("Imputado desde el menú contextual:", self.seleccionado)
        else:
            # Imputar todos los elementos con checkbox marcado
            items_a_imputar = [item for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "✔"]

            if items_a_imputar:
                # self.cursor.executemany("""
                #     UPDATE registros
                #     SET state = 'imputado', fecha_imputacion = ?
                #     WHERE id = ?
                # """, [(fecha_actual, item) for item in items_a_imputar])
                # self.conexion.commit()
                # # Eliminar del Treeview
                # for item in items_a_imputar:
                #     self.tree.delete(item)
                print("imputados desde checkbox los items: ", items_a_imputar)


