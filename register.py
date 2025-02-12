from functions import formatear_fecha, return_fecha_actual, seconds_to_string
from functions import DB_PATH
from sqlite import DatabaseManager
from treeview import TreeviewManager
import tkinter as tk
from tkinter import ttk

class TasksAdmin:
    def __init__(self, app):
        self.app = app
        self.session = app.session

        # Frame principal para la tabla y el scrollbar
        self.frame = ttk.Frame(app.root)

        self.db_manager = DatabaseManager(DB_PATH)
        self.treeview_manager = TreeviewManager(self)


    
    def cargar_datos_desde_sqlite(self):
        """
        Carga los registros existentes desde SQLite al Treeview filtrados por usuario.
        """
        self.treeview_manager.limpiar_tree()  # Limpia el Treeview antes de cargar nuevos datos

        # Obtener registros desde la base de datos usando DatabaseManager
        registros = self.db_manager.obtener_registros(self.session.user)

        for row in registros:
            # Datos originales
            tiempo_original = int(row["tiempo"])  # Tiempo en segundos
            fecha_original = row["fecha_creacion"]  # Fecha en formato YYYY-MM-DD HH:MM:SS

            # Convertir los datos al formato visual para la UI
            tiempo_formateado = seconds_to_string(tiempo_original, include_seconds=False)
            fecha_formateada = formatear_fecha(fecha_original)

            # Insertar en el Treeview con columnas visibles y ocultas
            # Delegar la inserción de la fila a TreeviewManager
            self.treeview_manager.agregar_fila(registro_id=row["id"], tiempo_formateado=tiempo_formateado,
                                               empresa=row["empresa"], concepto=row["concepto"], fecha_formateada=fecha_formateada,
                                               tiempo_original=tiempo_original, fecha_original=fecha_original)



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
            register_dic = self.db_manager.obtener_registro(registro_id)

            if register_dic != None:
                # Recuperar datos del registro
                self.app.restored_task(register_dic["id"], register_dic["tiempo"], register_dic["empresa"], register_dic["concepto"])
            else:
                print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
                return

            # Forzar la deselección después del clic (evita el gris)
            self.treeview_manager.deseleccionar_fila()

        except Exception as e:
            print(f"Error al recuperar información de la fila {item}: {e}")

    
    def agregar_fila(self, time, empresa, concepto):
        """
        Agrega una fila nueva al Treeview y a la base de datos.
        Retorna el id de registro generado por sqlite
        """
        registro_id = self.db_manager.agregar_registro(time, empresa, concepto, self.session.user, self.session.department)
        fecha_formateada = formatear_fecha(return_fecha_actual())
        tiempo_formateado = seconds_to_string(time, include_seconds=False)
        self.treeview_manager.agregar_fila(registro_id, tiempo_formateado, empresa, concepto, fecha_formateada, time, return_fecha_actual())
        return registro_id



    def time_update(self, id_registro, time):
        """
        Actualiza el tiempo de un registro en el Treeview y en la base de datos.
        """
        self.db_manager.actualizar_registro(id_registro, tiempo=time)
        registro = self.db_manager.obtener_registro(id_registro)
        if registro:
            tiempo_formateado = seconds_to_string(time, include_seconds=False)
            fecha_formateada = formatear_fecha(registro["fecha_creacion"])
            self.treeview_manager.actualizar_fila(id_registro, tiempo_formateado, registro["empresa"], registro["concepto"], fecha_formateada, time, registro["fecha_creacion"])

    def borrar(self, desde_menu=False):
        """
        Borra una fila seleccionada o todas las filas con checkbox marcado.
        """
        if desde_menu:
            if self.treeview_manager.seleccionado:
                self.db_manager.borrar_registro(self.treeview_manager.seleccionado)
                self.treeview_manager.borrar_fila(self.treeview_manager.seleccionado)
        else:
            items_a_borrar = [item for item in self.treeview_manager.tree.get_children() if self.treeview_manager.tree.item(item, "values")[0] == "✔"]
            for item in items_a_borrar:
                self.db_manager.borrar_registro(item)
                self.treeview_manager.borrar_fila(item)


    def editar(self):
        """
        Muestra un popup dentro de la ventana principal sin oscurecer el fondo.
        """
        if not self.treeview_manager.seleccionado:
            print("No hay un registro seleccionado para editar.")
            return

        # Obtener el registro del id (iid del Treeview)
        registro_id = int(self.treeview_manager.seleccionado)
        registro_dic = self.db_manager.obtener_registro(registro_id)

        if registro_dic is None:
            print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
            return

        # Crear el frame del popup superpuesto sobre la ventana principal
        popup = tk.Frame(self.app.root, bg="white", relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
        popup.place(relx=0.5, rely=0.5, anchor="center")

        # Bloquear interacciones fuera del popup
        popup.grab_set()

        entries = {}
        labels = [
            "Tiempo (segundos):", "Empresa:", "Concepto:", "Fecha Creación:", 
            "Fecha Imputación:", "Estado:", "Usuario:", "Departamento:"
        ]
        campos = ["tiempo", "empresa", "concepto", "fecha_creacion", 
                "fecha_imputacion", "state", "user", "departamento"]

        # Crear los widgets con grid()
        for i, label_text in enumerate(labels):
            tk.Label(popup, text=label_text, bg="white", anchor="w").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = tk.Entry(popup, width=30)

            # Convertir valores a cadenas y manejar None
            value = str(registro_dic.get(campos[i], "") or "")
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entries[campos[i]] = entry

        def cerrar_popup():
            """ Libera la ventana principal y cierra el popup """
            popup.grab_release()
            popup.destroy()

        def guardar_cambios():
            """ Guarda los cambios en la base de datos y en el Treeview """
            nuevos_valores = {campo: entry.get() for campo, entry in entries.items()}

            # Usar la función actualizar_registro de DatabaseManager
            self.db_manager.actualizar_registro(registro_id, nuevos_valores=nuevos_valores)

            # Actualizar en el Treeview solo los valores visibles
            tiempo_formateado = seconds_to_string(int(nuevos_valores["tiempo"]), include_seconds=False)
            fecha_formateada = formatear_fecha(nuevos_valores["fecha_creacion"])
            self.treeview_manager.actualizar_fila(registro_id, tiempo_formateado, nuevos_valores["empresa"], 
                                                nuevos_valores["concepto"], fecha_formateada, nuevos_valores["tiempo"],
                                                nuevos_valores["fecha_creacion"])

            # Cerrar popup y restaurar la ventana principal
            cerrar_popup()

        # Botones alineados horizontalmente
        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        btn_guardar = tk.Button(btn_frame, text="Guardar", command=guardar_cambios, bg="#4CAF50", fg="white", width=12)
        btn_guardar.pack(side=tk.LEFT, padx=5)

        btn_cancelar = tk.Button(btn_frame, text="Cerrar", command=cerrar_popup, bg="#f44336", fg="white", width=12)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)





    def imputar(self, desde_menu=False):
        """
    Imputa registros desde SQLite y los sube a SQL Server.
    - Si `desde_menu` es True, imputa solo un registro seleccionado.
    - Si `desde_menu` es False, imputa todos los registros con checkbox marcado.
    """
    fecha_actual = return_fecha_actual()
    print("🔹 Iniciando proceso de imputación...")

    # Conexión a SQLite
    conexion_sqlite = sqlite3.connect("base_local.db")  # Reemplaza con tu BD real
    cursor_sqlite = conexion_sqlite.cursor()

    # Obtener los registros a imputar
    items_a_imputar = []

    if desde_menu:
        if self.treeview_manager.seleccionado:
            items_a_imputar.append(self.treeview_manager.seleccionado)
    else:
        items_a_imputar = [item for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "✔"]

    if not items_a_imputar:
        print("⚠️ No hay registros seleccionados para imputar.")
        return

    print(f"📂 Registros a imputar: {items_a_imputar}")

    # Paso 1: Actualizar SQLite antes de enviar a SQL Server
    cursor_sqlite.executemany("""
        UPDATE registros
        SET fecha_imputacion = ?, state = 'imputado'
        WHERE id = ?
    """, [(fecha_actual, item) for item in items_a_imputar])
    conexion_sqlite.commit()

    # Obtener los datos de los registros imputados para SQL Server
    placeholders = ",".join(["?" for _ in items_a_imputar])  # Genera '?, ?, ?' según la cantidad de registros
    cursor_sqlite.execute(f"""
        SELECT tiempo, empresa, concepto, fecha_creacion, fecha_imputacion, state, user, departamento, ''
        FROM registros
        WHERE id IN ({placeholders})
    """, items_a_imputar)
    datos_a_subir = cursor_sqlite.fetchall()

    if not datos_a_subir:
        print("⚠️ No se encontraron datos para subir a SQL Server.")
        return

    # Paso 2: Subir datos a SQL Server
    if insertar_registros(datos_a_subir):
        # Paso 3: Confirmar en SQLite que los registros fueron imputados correctamente
        cursor_sqlite.executemany("""
            UPDATE registros
            SET state = 'imputado'
            WHERE id = ?
        """, [(item,) for item in items_a_imputar])
        conexion_sqlite.commit()

        print(f"✅ Registros {items_a_imputar} imputados correctamente en SQL Server y actualizados en SQLite.")

    # Cerrar conexiones
    conexion_sqlite.close()

    # Eliminar registros de la interfaz gráfica
    for item in items_a_imputar:
        self.tree.delete(item)

    print("🚀 Imputación completada.")







    def pack_forget(self):
        """
        Oculta el Treeview y su contenedor.
        """
        self.frame.pack_forget()  # Oculta el frame completo

    def pack(self):
        """
        Muestra el Treeview y su contenedor.
        """
        self.frame.pack(fill="both", expand=True)  # Muestra el frame completo

        
