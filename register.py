from functions import formatear_fecha, return_fecha_actual, seconds_to_string
from search_frame import BusquedaFrame
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
        self.treeview_manager = TreeviewManager(self)


    def cargar_datos_desde_sqlite(self):
        """
        Carga los registros existentes desde SQLite al Treeview filtrados por usuario.
        """
        self.treeview_manager.limpiar_tree()  # Limpia el Treeview antes de cargar nuevos datos

        # Obtener registros desde la base de datos usando DatabaseManager
        registros = self.app.db_manager.obtener_registros(self.session.user)

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
            #print("Error: Se intentó recuperar un ítem inválido.")
            return

        try:
            # Recuperar datos del registro de la base de datos
            registro_id = str(item)
            register_dic = self.app.db_manager.obtener_registro(registro_id)

            #print(register_dic)

            if register_dic != None:
                # Recuperar datos del registro
                self.app.restored_task(register_dic)
            else:
                #print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
                return

        except Exception as e:
            #print(f"Error al recuperar información de la fila {item}: {e}")
            pass

    
    def nuevo_registro(self, time, register_dic):
        """
        Agrega una fila nueva al Treeview y a la base de datos.
        Retorna el id y fecha_creacion de registro generado por sqlite
        """
        
        registro_id = self.app.db_manager.agregar_registro(time, register_dic, self.session.user, self.session.department)
        fecha_formateada = formatear_fecha(register_dic["fecha_creacion"])
        tiempo_formateado = seconds_to_string(time, include_seconds=False)
        self.treeview_manager.agregar_fila(registro_id, tiempo_formateado, register_dic["empresa"], register_dic["concepto"], 
                                           fecha_formateada, time, register_dic["fecha_creacion"])

        return registro_id


    def update_register(self, register_dic, time):
        """
        Actualiza el tiempo de un registro en el Treeview y en la base de datos.
        """
        #print(register_dic)
        self.app.db_manager.actualizar_registro(nuevos_valores=register_dic, tiempo=time)


        if register_dic:
            tiempo_formateado = seconds_to_string(time, include_seconds=False)
            fecha_formateada = formatear_fecha(register_dic["fecha_creacion"])
            self.treeview_manager.actualizar_fila(register_dic["id"], tiempo_formateado, register_dic["empresa"], 
                                                  register_dic["concepto"], fecha_formateada, time, register_dic["fecha_creacion"])


    def borrar(self, desde_menu=False):
        """
        Borra una fila seleccionada o todas las filas con checkbox marcado, con confirmación previa.
        """
        pregunta = "¿Estás segur@ de que deseas borrar este registro?"
        if desde_menu:
            if self.treeview_manager.seleccionado:
                confirmacion = messagebox.askyesno("Confirmación", pregunta)
                if confirmacion:
                    self.app.db_manager.borrar_registro(self.treeview_manager.seleccionado)
                    self.treeview_manager.borrar_fila(self.treeview_manager.seleccionado)
        else:
            items_a_borrar = [item for item in self.treeview_manager.tree.get_children() if self.treeview_manager.tree.item(item, "values")[0] == "✔"]

            if not items_a_borrar:  # Si no hay registros seleccionados, no hacer nada
                messagebox.showinfo("Información", "No hay registros seleccionados para borrar.")
                return
            
            if len(items_a_borrar) > 1: pregunta = f"¿Estás segur@ de que deseas borrar {len(items_a_borrar)} registros?"
            confirmacion = messagebox.askyesno("Confirmación", pregunta)
            if confirmacion:
                for item in items_a_borrar:
                    self.app.db_manager.borrar_registro(item)
                    self.treeview_manager.borrar_fila(item)

                # Ocultar el frame inferior solo si hay elementos eliminados
                self.treeview_manager.bottom_frame.pack_forget()

        # Configurar estado inicial para empresa no seleccionada
        self.app.unselected_partner()


    def editar(self):
        """
        Muestra un popup dentro de la ventana principal sin oscurecer el fondo,
        permitiendo editar los campos en el siguiente orden:
        Empresa, Usuario, Departamento, Concepto, descripcion, Fecha Creación y Tiempo.
        La hora original de 'fecha_creacion' se conserva sin que el usuario la modifique.
        """
        if not self.treeview_manager.seleccionado:
            #print("No hay un registro seleccionado para editar.")
            return

        registro_id = int(self.treeview_manager.seleccionado)
        registro_dic = self.app.db_manager.obtener_registro(registro_id)

        if registro_dic is None:
            #print(f"No se encontró el registro en la base de datos para el ID {registro_id}.")
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

        # 5. descripcion (nuevo, editable, dos líneas; no se muestra en el treeview)
        tk.Label(popup, text="Descripción:", bg="white", anchor="nw").grid(row=4, column=0, sticky="nw", padx=5, pady=2)
        text_descripcion = tk.Text(popup, width=30, height=2)
        text_descripcion.insert("1.0", str(registro_dic.get("descripcion", "")))
        text_descripcion.grid(row=4, column=1, padx=5, pady=2)
        entries["descripcion"] = text_descripcion

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
            descripcion = text_descripcion.get("1.0", "end-1c")  # Obtiene el texto completo sin el salto de línea final
            
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
                "id": registro_id,
                "concepto": concepto,
                "descripcion": descripcion,
                "fecha_creacion": nueva_fecha,
                "tiempo": nuevo_tiempo
            }
            self.app.db_manager.actualizar_registro(nuevos_valores=nuevos_valores)

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

    
    def set_imputacion(self, register_dic):
        fecha_actual = return_fecha_actual()
        register_dic["fecha_imputacion"] = fecha_actual
        register_dic["state"] = "imputando"
        self.app.db_manager.actualizar_registro(nuevos_valores=register_dic)




    def imputar(self, desde_menu=False):
        """
        Imputa registros desde SQLite y los sube a SQL Server.
        - Si `desde_menu` es True, imputa solo un registro seleccionado.
        - Si `desde_menu` es False, imputa todos los registros con checkbox marcado.
        """

        #print("🔹 Iniciando proceso de imputación...")

        # Obtener los registros a imputar
        items_a_imputar = []

        if desde_menu:
            if self.treeview_manager.seleccionado:
                items_a_imputar.append(self.treeview_manager.seleccionado)
        else:
            items_a_imputar = [item for item in self.treeview_manager.tree.get_children() if 
                               self.treeview_manager.tree.item(item, "values")[0] == "✔"]

        if not items_a_imputar:
            #print("⚠️ No hay registros seleccionados para imputar.")
            return
        
        # Definir el mensaje de confirmación
        if len(items_a_imputar) == 1:
            pregunta = "¿Estás segur@ que deseas imputar este registro?"
        else:
            pregunta = f"¿Estás segur@ que deseas imputar estos {len(items_a_imputar)} registros?"

        respuesta_usuario = messagebox.askyesno("Confirmación de Imputación", pregunta, parent=self.app.root)
        if not respuesta_usuario:
            #print("🚫 Imputación cancelada por el usuario.")
            return


        #print(f"📂 Registros a imputar: {items_a_imputar}")

        imputados = []
        for item_id in items_a_imputar:
            register_dic = self.app.db_manager.obtener_registro(item_id)
            
            if register_dic["vinculada"]:
                self.set_imputacion(register_dic)
                imputados.append(item_id)
            else: #empresa a imputar sin crear en sistemas
                respuesta = messagebox.askyesno("Advertencia",
                                                "No se pueden imputar empresas no creadas en sistemas.\n\n"
                                                "Para poderla imputar, tiene que vincular la empresa temporal a una real.\n\n"
                                                "¿Desea vincular la empresa ahora?",
                                                parent=self.app.root)  # Centrar en la ventana principal
                if respuesta:  # Si elige "Vincular"
                    popup = VinculacionPopup(self, self.app.root, self.session, register_dic)
                    self.app.root.wait_window(popup)
                    
                    #print("popup.vinculado:", popup.vinculado)

                    if popup.vinculado:
                        #volvemos a leer los datos cambiados en la clase VinculacionPopup
                        register_dic = self.app.db_manager.obtener_registro(item_id)
                        self.set_imputacion(register_dic)
                        imputados.append(item_id)
                else:
                    # Si elige "Cerrar", simplemente se cierra el mensaje sin hacer nada
                    self.app.unselected_partner()
                    return


        if len(imputados) != 0:
            #recarreguem el treeview amb les noves dades
            self.cargar_datos_desde_sqlite()

            #miramos y subimos si hay registros imputando (pendientes de imputar en el sqlserver) para el usuario
            self.app.sql_server_manager.subir_registros(self.app.db_manager, self.app.session.user)

            self.treeview_manager.bottom_frame.pack_forget()
            self.app.unselected_partner()

            #print("🚀 Imputación completada.")





class VinculacionPopup(tk.Toplevel):
    def __init__(self, tasks_admin, root, session, empresa_temp_dic):
        super().__init__(root)

        self.vinculado = False
        
        self.tasks_admin = tasks_admin
        self.db_manager = tasks_admin.app.db_manager
        self.empresa_temp_dic = empresa_temp_dic

        self.title("Vincular tarea a empresa real")

        # Centrar la ventana en la pantalla
        self.update_idletasks()  # Asegura que las dimensiones son correctas antes de posicionar
        ancho_ventana = 700
        alto_ventana = 200

        # Obtener dimensiones de la ventana principal (root)
        ancho_pantalla = root.winfo_width()
        alto_pantalla = root.winfo_height()
        pos_x = root.winfo_x() + (ancho_pantalla // 2) - (ancho_ventana // 2)
        pos_y = root.winfo_y() + (alto_pantalla // 2) - (alto_ventana // 2)

        # Aplicar nueva posición
        self.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")

        # Hace que el popup sea modal (bloquea la ventana principal)
        self.transient(root)
        self.grab_set()
        self.focus_set() # Mantiene el popup en primer plano y enfocado

        # Extraer datos de empresa y cif del diccionario de empresa temporal
        empresa_nombre = self.empresa_temp_dic.get("empresa", "Desconocida")  # Si no existe, pone "Desconocida"
        empresa_cif = self.empresa_temp_dic.get("cif", "N/A")  # Si no existe, pone "N/A"
        
        # Frame para la información de la empresa temporal
        frame_temp = tk.Frame(self)
        frame_temp.pack(pady=10, padx=10, fill="x")

        # Etiqueta Empresa
        label_empresa = tk.Label(frame_temp, text=f"Empresa: {empresa_nombre}", font=("Arial", 10, "bold"))
        label_empresa.pack(anchor="w")

        # Etiqueta CIF
        label_cif = tk.Label(frame_temp, text=f"CIF: {empresa_cif}", font=("Arial", 10))
        label_cif.pack(anchor="w")

        # Frame de búsqueda para la empresa real (parte inferior)
        self.frame_real = BusquedaFrame(self, session, "Empresa:", callback=None)
        self.frame_real.pack(pady=10, padx=10, fill="x")

        #rellenamos el frame_real con empresas reales
        self.empresas_dic = session.return_empresas_combo_values(todas=False, create=False)
        self.frame_real.configurar_combobox(self.empresas_dic, seleccion="Selecciona Empresa")
        
        # Botón de confirmación
        btn_confirmar = ttk.Button(self, text="Confirmar", command=self.confirmar)
        btn_confirmar.pack(pady=10)


    def confirmar(self):
        empresa_real = self.frame_real.combobox.get()

        # Obtener el CIF de la empresa real desde el diccionario interno
        cif_real = self.empresas_dic.get(empresa_real)

        #vinculamos todos los valores de la nueva empresa temporal en la base de datos de registros
        self.db_manager.vincular_empresa(self.empresa_temp_dic["empresa"], empresa_real, cif_real)

        self.vinculado = True

        # Verificar antes de destruir la ventana
        if self.winfo_exists():
            self.destroy()