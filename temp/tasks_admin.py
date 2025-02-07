import tkinter as tk
from tkinter import ttk, Menu
import sqlite3
from functions import formatear_fecha, return_fecha_actual, seconds_to_string

db_path = r"data/treeview_data.db"

class TasksAdmin:
    def __init__(self, root, app, manager):
        self.app = app
        self.manager = manager

        self.menu_habilitado = True  # Variable para controlar si el menú está habilitado
        self.seleccionado = None # Variable para mantener el registro seleccionado

        # Conectar a SQLite
        self.conexion = sqlite3.connect(db_path)
        self.cursor = self.conexion.cursor()
        self._crear_tabla()

        # Frame principal para la tabla y el scrollbar
        self.frame = ttk.Frame(root)
        #self.frame.pack(fill=tk.BOTH, expand=True)

        # Treeview (tabla)
        self.tree = ttk.Treeview(self.frame, columns=("tiempo", "empresa", "tarea", "fecha"), 
                                 show="headings", height=10)

        # Encabezados de las columnas
        self.tree.heading("tiempo", text="Tiempo")
        self.tree.heading("empresa", text="Empresa")
        self.tree.heading("tarea", text="Tarea")
        self.tree.heading("fecha", text="Fecha")

        # Configuración de columnas
        self.tree.column("tiempo", width=80, anchor="center", stretch=True)
        self.tree.column("empresa", width=150, anchor="center", stretch=True)
        self.tree.column("tarea", width=200, anchor="center", stretch=True)
        self.tree.column("fecha", width=150, anchor="center", stretch=True)

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

        # Evento de clic derecho (menu contextual)
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)

        # Crear el menú contextual
        self.menu_contextual = Menu(root, tearoff=0)
        self.menu_empresa = self.menu_contextual.add_command(label="", state=tk.DISABLED)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Recuperar", command=self.recuperar)
        self.menu_contextual.add_command(label="Editar", command=self.editar)
        self.menu_contextual.add_command(label="Borrar", command=self.borrar)
        self.menu_contextual.add_command(label="Imputar", command=self.imputar)

        # Cargar datos iniciales desde SQLite
        # self.cargar_datos_desde_sqlite()

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
            # Actualizar la etiqueta del menú contextual para mostrar solo el nombre de la empresa
            self.menu_contextual.entryconfigure(0, label=valores[1])
            self.menu_contextual.post(event.x_root, event.y_root)
        else:
            self.seleccionado = None


    def color_fila_superior(self, color="white"):
        """
        Cambia el color de la fila superior del Treeview al color especificado.
        """
        # Obtener la fila superior (primer hijo del Treeview)
        children = self.tree.get_children()
        if children:  # Asegurarse de que el Treeview no esté vacío
            fila_superior = children[0]

            # Asignar un "tag" a la fila superior
            self.tree.item(fila_superior, tags=(color,))

            # Configurar el color para el "tag" 'highlight'
            self.tree.tag_configure(color, background=color)


    def _crear_tabla(self):
        """
        Crea la tabla en SQLite si no existe.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tiempo TEXT,
                empresa TEXT,
                tarea TEXT,
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
            SELECT id, tiempo, empresa, tarea, fecha_creacion
            FROM registros 
            WHERE state = 'working' AND user = ?
        """, (self.manager.user,))
        for row in self.cursor.fetchall():
            # Formatear la fecha de creación y tiempo empleado antes de mostrarlos
            fecha_formateada = formatear_fecha(row[4])
            time = seconds_to_string(row[1], include_seconds=False)
            # Usar el id como iid en el Treeview
            self.tree.insert("", "end", iid=row[0], values=(time, row[2], row[3], fecha_formateada))

    def agregar_fila(self, time, empresa, tarea):
        """
        Agrega una fila nueva al Treeview (arriba) y a SQLite en cuanto iniciamos la tarea
        """
        # Fecha actual
        fecha_actual = return_fecha_actual()

        # Insertar en SQLite
        self.cursor.execute("""
            INSERT INTO registros (tiempo, empresa, tarea, fecha_creacion, fecha_imputacion, state, user, departamento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (time, empresa, tarea, fecha_actual, None, "working", self.manager.user, self.manager.department))
        self.conexion.commit()
        row_id = self.cursor.lastrowid  # Obtener el id generado por SQLite

        # Insertar en el Treeview al inicio con la fecha y tiempo formateada
        fecha_formateada = formatear_fecha(fecha_actual)
        time = seconds_to_string(time, include_seconds=False)
        self.tree.insert("", 0, iid=row_id, values=(time, empresa, tarea, fecha_formateada))


    def time_update(self, time):
        """
        Actualiza el campo 'tiempo' del registro en la parte superior del Treeview
        y lo sincroniza con la base de datos.

        Parámetros:
            time (str): Nuevo valor para el campo 'tiempo'.
        """

        # Obtener la fila superior (primer hijo del Treeview)
        children = self.tree.get_children()
        if not children:
            print("No hay registros en el Treeview.")
            return

        # Obtener el id de la fila superior
        fila_superior_id = children[0]

        # Obtener los valores actuales de la fila superior
        valores_actuales = self.tree.item(fila_superior_id)["values"]
        empresa_actual = valores_actuales[1]  # Mantener el valor de 'empresa'
        tarea_actual = valores_actuales[2]   # Mantener el valor de 'tarea'
        fecha_actual = valores_actuales[3]   # Mantener el valor de 'fecha'

        # Actualizar la base de datos
        self.cursor.execute("""
            UPDATE registros
            SET tiempo = ?
            WHERE id = ?
        """, (time, fila_superior_id))
        self.conexion.commit()

        time = seconds_to_string(time, include_seconds=False)

        # Actualizar el Treeview
        nuevos_valores = (time, empresa_actual, tarea_actual, fecha_actual)
        self.tree.item(fila_superior_id, values=nuevos_valores)



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


    def recuperar(self):
        """
        Acción para recuperar datos de la fila seleccionada.
        Mueve la fila seleccionada al principio del Treeview y recupera la información de la base de datos.
        """
        if self.seleccionado:
            # Obtener los valores actuales de la fila seleccionada
            valores = self.tree.item(self.seleccionado)["values"]
            
            # Eliminar y reinsertar la fila al principio del Treeview
            self.tree.delete(self.seleccionado)
            self.tree.insert("", 0, values=valores, iid=self.seleccionado)

            # Obtener el ID del registro seleccionado
            registro_id = int(self.seleccionado)

            # Recuperar la información del registro desde la base de datos
            self.cursor.execute("""
                SELECT id, tiempo, empresa, tarea, fecha_creacion, fecha_imputacion, state, user, departamento
                FROM registros
                WHERE id = ?
            """, (registro_id,))
            registro = self.cursor.fetchone()

            if registro:
                # Extraer los campos del registro en variables
                (id_registro, time, empresa, tarea, fecha_creacion, fecha_imputacion, state, user, departamento) = registro

                # Ahora puedes usar estas variables como necesites
                print(f"ID: {id_registro}")
                print(f"Tiempo: {time}")
                print(f"Empresa: {empresa}")
                print(f"Tarea: {tarea}")
                print(f"Fecha de creación: {fecha_creacion}")
                print(f"Fecha de imputación: {fecha_imputacion}")
                print(f"Estado: {state}")
                print(f"Usuario: {user}")
                print(f"Departamento: {departamento}")
                    # AQUI CRIDAREM A UNA FUNCIO QUE UBICARA LES DADES AL TOOGLE PER REANUDAR AMB LA TASCA
                    # EN PRINCIPI PENSO EN UBICAR EMPRESA Y TEMPS FORMATEJAT Y CAMBIAR VARIABLES RUNNING, PAUSED(VISUALS) Y TIME_ELAPSED(FUNCIONAL)
            else:
                print("No se encontró el registro en la base de datos.")

            self.app.restored_task(id_registro, time, empresa, tarea)

    def editar(self):
        """
        Acción para editar datos de la fila seleccionada.
        """
        if self.seleccionado:
            # Obtener el id (iid del Treeview)
            registro_id = int(self.seleccionado)
            
            # Obtener los valores actuales del Treeview
            valores = self.tree.item(self.seleccionado)["values"]
            print(f"Valores en el Treeview: {valores} (ID: {registro_id})")

            # Obtener el registro correspondiente de la base de datos
            self.cursor.execute("""
                SELECT id, tiempo, empresa, tarea, fecha_creacion, fecha_imputacion, state, user
                FROM registros
                WHERE id = ?
            """, (registro_id,))
            registro = self.cursor.fetchone()
            if registro:
                print(f"Registro en la base de datos: {registro}")

            # Ejemplo: Abrir un formulario para editar los datos
            nuevo_tiempo = valores[0]
            nueva_empresa = valores[1]
            nueva_tarea = valores[2]

            # Actualizar en SQLite
            self.cursor.execute("""
                UPDATE registros
                SET tiempo = ?, empresa = ?, tarea = ?
                WHERE id = ?
            """, (nuevo_tiempo, nueva_empresa, nueva_tarea, registro_id))
            self.conexion.commit()

            # Actualizar el Treeview (si es necesario)
            self.tree.item(self.seleccionado, values=(nuevo_tiempo, nueva_empresa, nueva_tarea, valores[3]))


    def borrar(self):
        """
        Acción para borrar la fila seleccionada.
        """
        if self.seleccionado:
            # Eliminar de SQLite
            self.cursor.execute("DELETE FROM registros WHERE id = ?", (self.seleccionado,))
            self.conexion.commit()

            # Eliminar del Treeview
            self.tree.delete(self.seleccionado)
            self.seleccionado = None

    def imputar(self):
        """
        Acción para imputar datos de la fila seleccionada.
        Cambia el estado a 'imputado' en SQLite y elimina la fila del Treeview.
        """
        if self.seleccionado:
            fecha_actual = return_fecha_actual()
            # Actualizar SQLite
            self.cursor.execute("""
                UPDATE registros
                SET state = 'imputado', fecha_imputacion = ?
                WHERE id = ?
            """, (fecha_actual, self.seleccionado))
            self.conexion.commit()

            # Eliminar del Treeview
            self.tree.delete(self.seleccionado)
            self.seleccionado = None

