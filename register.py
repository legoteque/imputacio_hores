from functions import formatear_fecha, return_fecha_actual, seconds_to_string
from functions import DB_PATH
from sqlite import DatabaseManager
from treeview import TreeviewManager
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
from datetime import datetime

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
            fecha_original = row["fecha_creacion"]  # Fecha en formato YYYY-MM-DD HH:MM

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

            print(register_dic)

            if register_dic != None:
                # Recuperar datos del registro
                self.app.restored_task(register_dic)
            else:
                print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
                return

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
            #ocultamos el frame inferior
            self.treeview_manager.bottom_frame.pack_forget()

        #configuramos estado inicial para empresa no seleccionada
        self.app.unselected_partner()


    
    def imputar(self, desde_menu=False):
        """
        Imputa registros desde SQLite y los sube a SQL Server.
        - Si `desde_menu` es True, imputa solo un registro seleccionado.
        - Si `desde_menu` es False, imputa todos los registros con checkbox marcado.
        """
        fecha_actual = return_fecha_actual()
        print("🔹 Iniciando proceso de imputación...")

        # Obtener los registros a imputar
        items_a_imputar = []

        if desde_menu:
            if self.treeview_manager.seleccionado:
                items_a_imputar.append(self.treeview_manager.seleccionado)
        else:
            items_a_imputar = [item for item in self.treeview_manager.tree.get_children() if 
                               self.treeview_manager.tree.item(item, "values")[0] == "✔"]

        if not items_a_imputar:
            print("⚠️ No hay registros seleccionados para imputar.")
            return

        print(f"📂 Registros a imputar: {items_a_imputar}")

        # Paso 1: Actualizar estado en SQLite a "imputando"
        for item_id in items_a_imputar:
            self.db_manager.actualizar_registro(
                item_id,
                nuevos_valores={"fecha_imputacion": fecha_actual, "state": "imputando"}
            )

        # Eliminar registros de la interfaz gráfica
        for item in items_a_imputar:
            self.treeview_manager.borrar_fila(item)

        #ocultamos el frame inferior
        self.treeview_manager.bottom_frame.pack_forget()
        
        #configuramos estado inicial para empresa no seleccionada
        self.app.unselected_partner()

        print("🚀 Imputación completada.")



    def editar(self):
        """
        Muestra un popup dentro de la ventana principal sin oscurecer el fondo,
        permitiendo editar los campos en el siguiente orden:
        Empresa, Usuario, Departamento, Concepto, Observaciones, Fecha Creación y Tiempo.
        La hora original de 'fecha_creacion' se conserva sin que el usuario la modifique.
        """
        if not self.treeview_manager.seleccionado:
            print("No hay un registro seleccionado para editar.")
            return

        registro_id = int(self.treeview_manager.seleccionado)
        registro_dic = self.db_manager.obtener_registro(registro_id)

        if registro_dic is None:
            print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
            return

        popup = tk.Frame(self.app.root, bg="white", relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
        popup.place(relx=0.5, rely=0.5, anchor="center")
        popup.grab_set()

        entries = {}

        # 1. Empresa (no editable)
        tk.Label(popup, text="Empresa:", bg="white", anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        entry_empresa = tk.Entry(popup, width=30)
        entry_empresa.insert(0, str(registro_dic.get("empresa", "")))
        entry_empresa.config(state="disabled")
        entry_empresa.grid(row=0, column=1, padx=5, pady=2)
        entries["empresa"] = entry_empresa

        # 2. Usuario (no editable)
        tk.Label(popup, text="Usuario:", bg="white", anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        entry_user = tk.Entry(popup, width=30)
        entry_user.insert(0, str(registro_dic.get("user", "")))
        entry_user.config(state="disabled")
        entry_user.grid(row=1, column=1, padx=5, pady=2)
        entries["user"] = entry_user

        # 3. Departamento (no editable)
        tk.Label(popup, text="Departamento:", bg="white", anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        entry_departamento = tk.Entry(popup, width=30)
        entry_departamento.insert(0, str(registro_dic.get("departamento", "")))
        entry_departamento.config(state="disabled")
        entry_departamento.grid(row=2, column=1, padx=5, pady=2)
        entries["departamento"] = entry_departamento

        # 4. Concepto (editable)
        tk.Label(popup, text="Concepto:", bg="white", anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        entry_concepto = tk.Entry(popup, width=30)
        entry_concepto.insert(0, str(registro_dic.get("concepto", "")))
        entry_concepto.grid(row=3, column=1, padx=5, pady=2)
        entries["concepto"] = entry_concepto

        # 5. Observaciones (nuevo, editable, dos líneas; no se muestra en el treeview)
        tk.Label(popup, text="Observaciones:", bg="white", anchor="nw").grid(row=4, column=0, sticky="nw", padx=5, pady=2)
        text_observaciones = tk.Text(popup, width=30, height=2)
        text_observaciones.insert("1.0", str(registro_dic.get("observaciones", "")))
        text_observaciones.grid(row=4, column=1, padx=5, pady=2)
        entries["observaciones"] = text_observaciones

        # 6. Fecha Creación (editar día, mes y año; conservar hora original)
        tk.Label(popup, text="Fecha Creación:", bg="white", anchor="w").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        date_frame = tk.Frame(popup, bg="white")
        tk.Label(date_frame, text="Día:", bg="white").grid(row=0, column=0, padx=2, pady=2)
        spinbox_dia = tk.Spinbox(date_frame, from_=1, to=31, width=3)
        spinbox_dia.grid(row=0, column=1, padx=2, pady=2)
        tk.Label(date_frame, text="Mes:", bg="white").grid(row=0, column=2, padx=2, pady=2)
        spinbox_mes = tk.Spinbox(date_frame, from_=1, to=12, width=3)
        spinbox_mes.grid(row=0, column=3, padx=2, pady=2)
        tk.Label(date_frame, text="Año:", bg="white").grid(row=0, column=4, padx=2, pady=2)
        spinbox_anyo = tk.Spinbox(date_frame, from_=1900, to=2100, width=5)
        spinbox_anyo.grid(row=0, column=5, padx=2, pady=2)
        date_frame.grid(row=5, column=1, padx=5, pady=2)

        # Inicializar los spinboxes de la fecha utilizando 'fecha_creacion' (formato "YYYY-MM-DD HH:MM")
        fecha_actual = registro_dic.get("fecha_creacion", "")
        hora_original = "00:00"  # Valor por defecto
        try:
            partes = fecha_actual.split()
            fecha_solo = partes[0]  # "YYYY-MM-DD"
            if len(partes) > 1:
                time_part = partes[1]
                if time_part.count(":") >= 2:
                    dt_time = datetime.strptime(time_part, "%H:%M:%S")
                    hora_original = dt_time.strftime("%H:%M")
                else:
                    hora_original = time_part
            else:
                hora_original = "00:00"
            anyo_str, mes_str, dia_str = fecha_solo.split("-")
            spinbox_anyo.delete(0, tk.END)
            spinbox_anyo.insert(0, anyo_str)
            spinbox_mes.delete(0, tk.END)
            spinbox_mes.insert(0, str(int(mes_str)))
            spinbox_dia.delete(0, tk.END)
            spinbox_dia.insert(0, str(int(dia_str)))
        except Exception as e:
            spinbox_anyo.delete(0, tk.END)
            spinbox_anyo.insert(0, "2023")
            spinbox_mes.delete(0, tk.END)
            spinbox_mes.insert(0, "1")
            spinbox_dia.delete(0, tk.END)
            spinbox_dia.insert(0, "1")
            hora_original = "00:00"
        entries["dia"] = spinbox_dia
        entries["mes"] = spinbox_mes
        entries["anyo"] = spinbox_anyo

        # 7. Tiempo (editar con spinboxes; se muestra en horas y minutos)
        tk.Label(popup, text="Tiempo:", bg="white", anchor="w").grid(row=6, column=0, sticky="w", padx=5, pady=2)
        time_frame2 = tk.Frame(popup, bg="white")
        tk.Label(time_frame2, text="Horas:", bg="white").grid(row=0, column=0, padx=2, pady=2)
        spinbox_horas2 = tk.Spinbox(time_frame2, from_=0, to=23, width=5)
        spinbox_horas2.grid(row=0, column=1, padx=2, pady=2)
        tk.Label(time_frame2, text="Minutos:", bg="white").grid(row=0, column=2, padx=2, pady=2)
        # Usamos variable con validación para minutos
        minutos_var = tk.StringVar()
        spinbox_minutos2 = tk.Spinbox(time_frame2, from_=0, to=59, width=5, textvariable=minutos_var, wrap=True)
        spinbox_minutos2.grid(row=0, column=3, padx=2, pady=2)
        time_frame2.grid(row=6, column=1, padx=5, pady=2)

        # Función para validar que los minutos no excedan 59
        def validar_minutos(*args):
            try:
                value = int(minutos_var.get())
            except ValueError:
                return
            if value >= 60:
                minutos_var.set("0")
        minutos_var.trace_add("write", validar_minutos)

        # Inicializar spinboxes del tiempo (convertido de segundos a horas y minutos)
        tiempo_segundos = int(registro_dic.get("tiempo", 0))
        horas_t = tiempo_segundos // 3600
        minutos_t = (tiempo_segundos % 3600) // 60
        spinbox_horas2.delete(0, tk.END)
        spinbox_horas2.insert(0, str(horas_t))
        minutos_var.set(str(minutos_t))

        def cerrar_popup():
            #configuramos estado inicial para empresa no seleccionada
            self.app.unselected_partner()

            popup.grab_release()
            popup.destroy()

        def guardar_cambios():
            # Obtener valores ingresados por el usuario
            concepto = entry_concepto.get()
            observaciones = text_observaciones.get("1.0", "end-1c")  # Obtiene el texto completo sin el salto de línea final
            
            # Obtener fecha formateada con la hora original
            dia_val = int(spinbox_dia.get())
            mes_val = int(spinbox_mes.get())
            anyo_val = int(spinbox_anyo.get())
            nueva_fecha = f"{anyo_val:04d}-{mes_val:02d}-{dia_val:02d} {hora_original}"
            
            # Validar que la fecha introducida es correcta
            try:
                datetime.strptime(nueva_fecha, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Fecha inválida", "La fecha introducida no es válida. Por favor, revise los valores de día, mes y año.")
                return

            # Calcular el nuevo tiempo en segundos
            horas_val = int(spinbox_horas2.get())
            minutos_val = int(minutos_var.get())
            nuevo_tiempo = horas_val * 3600 + minutos_val * 60

            # Formatear el tiempo para mostrarlo en el Treeview
            tiempo_formateado = seconds_to_string(nuevo_tiempo, include_seconds=False)

            # Obtener la empresa (aunque sea no editable, se necesita para el treeview)
            empresa = entry_empresa.get()

            # Formatear la fecha para el Treeview (sin la hora si solo se muestra la fecha)
            fecha_formateada = formatear_fecha(nueva_fecha)
            
            # Valores a actualizar en la base de datos
            nuevos_valores = {
                "concepto": concepto,
                "observaciones": observaciones,
                "fecha_creacion": nueva_fecha,
                "tiempo": nuevo_tiempo
            }
            self.db_manager.actualizar_registro(registro_id, nuevos_valores=nuevos_valores)

            # Actualiza el Treeview con los valores recién ingresados
            self.treeview_manager.actualizar_fila(
                registro_id, 
                tiempo_formateado,  # Tiempo formateado en HH:MM
                empresa,  # Empresa (no editable, pero se debe mantener)
                concepto,  # Concepto (editable)
                fecha_formateada,  # Fecha formateada en DD/MM/YYYY
                nuevo_tiempo,  # Tiempo en segundos (si es necesario)
                nueva_fecha  # Fecha completa con hora original
            )

            cerrar_popup()

        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        btn_guardar = tk.Button(btn_frame, text="Guardar", command=guardar_cambios, bg="#4CAF50", fg="white", width=12)
        btn_guardar.pack(side=tk.LEFT, padx=5)
        btn_cancelar = tk.Button(btn_frame, text="Cerrar", command=cerrar_popup, bg="#f44336", fg="white", width=12)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)








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

        
