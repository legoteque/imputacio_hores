from functions import formatear_fecha, return_fecha_actual, seconds_to_string
from search_frame import BusquedaFrame
from treeview import TreeviewManager
import tkinter as tk
from tkinter import ttk
from functions import CustomMessageBox as messagebox
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
        Carga TODOS los registros desde SQLite al Treeview filtrados por usuario.
        Los registros 'working' aparecen arriba y son interactivos.
        Los registros 'imputado'/'imputando' aparecen abajo y no son interactivos.
        """
        self.treeview_manager.limpiar_tree()

        registros = self.app.db_manager.obtener_registros(self.session.user_id)

        for row in registros:
            tiempo_original = int(row["tiempo"])
            fecha_original = row["fecha_creacion"]
            estado = row["state"]

            tiempo_formateado = seconds_to_string(tiempo_original, include_seconds=False)
            fecha_formateada = formatear_fecha(fecha_original)
            concepto_descripcion = self.codigo_a_descripcion(row["concepto"])
            es_interactivo = (estado == 'working')

            self.treeview_manager.agregar_fila(
                registro_id=row["id"], 
                tiempo_formateado=tiempo_formateado,
                empresa=row["empresa"], 
                concepto=concepto_descripcion, 
                fecha_formateada=fecha_formateada,
                tiempo_original=tiempo_original, 
                fecha_original=fecha_original,
                es_interactivo=es_interactivo
            )


    def recuperar(self, item):
        """
        Recupera información de la fila seleccionada y maneja errores.
        """
        if not item:
            return

        try:
            # Recuperar datos del registro de la base de datos
            registro_id = str(item)
            register_dic = self.app.db_manager.obtener_registro(registro_id)

            if register_dic != None:
                # Recuperar datos del registro
                self.app.restored_task(register_dic)
            else:
                return

        except Exception as e:
            pass

    
    def nuevo_registro(self, time, register_dic):
        """
        Agrega una fila nueva al Treeview y a la base de datos.
        Recarga el TreeView para mantener el orden correcto.
        """
        
        registro_id = self.app.db_manager.agregar_registro(time, register_dic, self.session.user_id, self.session.department)
        
        self.cargar_datos_desde_sqlite()
        
        return registro_id


    def update_register(self, register_dic, time):
        """
        Actualiza el tiempo de un registro en el Treeview y en la base de datos.
        Recarga el TreeView para mantener el orden correcto.
        """
        self.app.db_manager.actualizar_registro(nuevos_valores=register_dic, tiempo=time)

        self.cargar_datos_desde_sqlite()
        
        if register_dic and "id" in register_dic:
            try:
                self.treeview_manager.tree.selection_set(str(register_dic["id"]))
                self.treeview_manager.tree.focus(str(register_dic["id"]))
            except:
                pass


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
            return

        registro_id = int(self.treeview_manager.seleccionado)
        registro_dic = self.app.db_manager.obtener_registro(registro_id)

        if registro_dic is None:
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




        # DESPUÉS:
        concepto_combobox = ttk.Combobox(popup, width=27, state="readonly")
        # Cargar conceptos disponibles
        if hasattr(self.app, 'conceptos_dict'):
            concepto_combobox["values"] = list(self.app.conceptos_dict.keys())
            # Buscar la descripción correspondiente al código
            concepto_codigo = str(registro_dic.get("concepto", ""))
            for desc, codigo in self.app.conceptos_dict.items():
                if codigo == concepto_codigo:
                    concepto_combobox.set(desc)
                    break

        concepto_combobox.grid(row=3, column=1, padx=5, pady=2)
        entries["concepto"] = concepto_combobox

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
            concepto_descripcion = concepto_combobox.get()
            concepto = self.app.conceptos_dict.get(concepto_descripcion, "") if concepto_descripcion else ""
            descripcion = text_descripcion.get("1.0", "end-1c")  # Obtiene el texto completo sin el salto de línea final

            # ✅ NUEVA VALIDACIÓN: Verificar concepto obligatorio
            empresa = entry_empresa.get()
            if not empresa.startswith('0') and not concepto:
                messagebox.showerror("Concepto requerido", 
                                "Debe seleccionar un concepto para esta empresa.\n"
                                "Solo las tareas internas pueden ir sin concepto.")
                return  # Salir sin guardar
            
            # Obtener fecha formateada con la hora original
            dia_val = int(spinbox_dia.get())
            mes_val = int(spinbox_mes.get())
            anyo_val = int(spinbox_anyo.get())
            nueva_fecha = f"{anyo_val:04d}-{mes_val:02d}-{dia_val:02d} {hora_original}"
            
            # Validar que la fecha introducida es correcta
            try:
                fecha_introducida = datetime.strptime(nueva_fecha, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Fecha inválida", "La fecha introducida no es válida. Por favor, revise los valores de día, mes y año.")
                return
            
            # Obtener fecha actual
            fecha_actual = datetime.now()
            
            # Validar que la fecha no es posterior al día de hoy
            if fecha_introducida.date() > fecha_actual.date():
                messagebox.showerror("Fecha futura", "No se pueden introducir fechas posteriores al día de hoy.")
                return
            
            # Calcular el mes anterior
            if fecha_actual.month == 1:
                mes_anterior = 12
                anyo_mes_anterior = fecha_actual.year - 1
            else:
                mes_anterior = fecha_actual.month - 1
                anyo_mes_anterior = fecha_actual.year
            
            # Validar que la fecha está dentro del rango permitido (mes actual o anterior)
            fecha_limite_inferior = datetime(anyo_mes_anterior, mes_anterior, 1).date()
            
            if fecha_introducida.date() < fecha_limite_inferior:
                messagebox.showerror(
                    "Fecha fuera de rango", 
                    f"Solo se pueden introducir fechas del mes actual ({fecha_actual.strftime('%B %Y')}) "
                    f"o del mes anterior ({datetime(anyo_mes_anterior, mes_anterior, 1).strftime('%B %Y')})."
                )
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
                concepto_descripcion,  # Concepto (editable)
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

    
    def insercion_manual(self):
        """
        Abre una ventana para insertar uno o varios registros manualmente.
        Reutiliza la lógica del editor pero adaptada para nuevos registros.
        """
        popup = InsercionManualPopup(self, self.app.root, self.session, self.app.empresas_dic, self.app.conceptos_dict)
        self.app.root.wait_window(popup)
        
        # Recargar datos después de cerrar la ventana
        if popup.registros_insertados > 0:
            self.cargar_datos_desde_sqlite()
            self.app.unselected_partner()


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

        # Obtener los registros a imputar
        items_a_imputar = []

        if desde_menu:
            if self.treeview_manager.seleccionado:
                items_a_imputar.append(self.treeview_manager.seleccionado)
        else:
            items_a_imputar = [item for item in self.treeview_manager.tree.get_children() if 
                               self.treeview_manager.tree.item(item, "values")[0] == "✔"]

        if not items_a_imputar:
            return
        
        # Definir el mensaje de confirmación
        if len(items_a_imputar) == 1:
            pregunta = "¿Estás segur@ que deseas imputar este registro?"
        else:
            pregunta = f"¿Estás segur@ que deseas imputar estos {len(items_a_imputar)} registros?"

        respuesta_usuario = messagebox.askyesno("Confirmación de Imputación", pregunta, parent=self.app.root)
        if not respuesta_usuario:
            return

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
            self.app.sql_server_manager.subir_registros(self.app.db_manager, self.app.session.user_id)

            self.treeview_manager.bottom_frame.pack_forget()
            self.app.unselected_partner()


    def codigo_a_descripcion(self, concepto_codigo):
        """
        Convierte un código de concepto a su descripción correspondiente.
        Si no encuentra el código, devuelve el código original.
        """
        
        if not concepto_codigo or not hasattr(self.app, 'conceptos_dict'):
            return concepto_codigo
        
        for desc, codigo in self.app.conceptos_dict.items():
            if codigo == concepto_codigo:
                return desc
        
        return concepto_codigo  # Si no se encuentra, devolver el código original




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





class InsercionManualPopup(tk.Toplevel):
    def __init__(self, tasks_admin, root, session, empresas_dic, conceptos_dict):
        super().__init__(root)
        
        self.tasks_admin = tasks_admin
        self.db_manager = tasks_admin.app.db_manager
        self.session = session
        self.empresas_dic = empresas_dic
        self.conceptos_dict = conceptos_dict
        self.registros_insertados = 0
        
        self.title("Inserción Manual de Registros")
        
        # Configurar ventana
        ancho_ventana = 800
        alto_ventana = 450
        
        # Centrar en la ventana principal
        self.update_idletasks()
        ancho_pantalla = root.winfo_width()
        alto_pantalla = root.winfo_height()
        pos_x = root.winfo_x() + (ancho_pantalla // 2) - (ancho_ventana // 2)
        pos_y = root.winfo_y() + (alto_pantalla // 2) - (alto_ventana // 2)
        
        self.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")
        self.configure(bg="white")
        
        # Deshabilitar redimensionamiento
        self.resizable(False, False)
        
        # Modal
        self.transient(root)
        self.grab_set()
        self.focus_set()
        
        # Manejar cierre con X
        self.protocol("WM_DELETE_WINDOW", self.cerrar_popup)
        
        self.crear_interfaz()
        self.resetear_campos()
    
    def crear_interfaz(self):
        """Crea la interfaz de inserción manual SIN scroll."""
        
        # Título
        titulo_frame = tk.Frame(self, bg="white")
        titulo_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(titulo_frame, text="📝 Inserción Manual de Registros", 
                font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack()
        
        # ✅ FRAME PRINCIPAL DIRECTO (SIN CANVAS NI SCROLL)
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.entries = {}
        
        # Crear campos
        self.crear_campos()
        
        # ✅ CREAR BOTONES AL FINAL
        self.crear_botones()
    
    def crear_campos(self):
        """Crea los campos del formulario."""
        
        # 1. Empresa (ahora ocupa 2 filas: empresa + cif)
        self.crear_campo_empresa(0)  # Filas 0 y 1
        
        # 2. Usuario (fila 2)
        self.crear_campo_texto(2, "Usuario:", self.session.user, editable=False)
        
        # 3. Departamento (fila 3)
        self.crear_campo_texto(3, "Departamento:", self.session.department, editable=False)
        
        # 4. Concepto (fila 4)
        self.crear_campo_concepto(4)
        
        # 5. Descripción (fila 5)
        self.crear_campo_descripcion(5)
        
        # 6. Fecha Creación (fila 6)
        self.crear_campo_fecha(6)
        
        # 7. Tiempo (fila 7)
        self.crear_campo_tiempo(7)
    
    def crear_campo_empresa(self, fila):
        """Campo específico para empresa con BusquedaFrame."""
        
        # ✅ IMPLEMENTAR: Crear BusquedaFrame
        self.empresa_frame = BusquedaFrame(self.content_frame, self.session, "Empresa:", 
                                          callback=self.on_empresa_selected)
        self.empresa_frame.grid(row=fila, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # ✅ CONFIGURAR CON TODAS LAS EMPRESAS
        empresas_suasor, empresas_completas = self.session.return_empresas_combo_values(todas=True, create=True)
        self.empresa_frame.configurar_combobox(empresas_completas, seleccion="Selecciona una empresa")
        
        # Actualizar referencia para acceso fácil
        self.entries["empresa"] = self.empresa_frame.combobox
        
        # CIF display (fila siguiente)
        tk.Label(self.content_frame, text="CIF:", bg="white", font=("Arial", 10)).grid(
            row=fila+1, column=0, sticky="w", padx=10, pady=5)
        
        cif_label = tk.Label(self.content_frame, text="-", bg="white", font=("Arial", 10, "bold"), 
                           fg="#34495e", width=20, relief="sunken", anchor="w")
        cif_label.grid(row=fila+1, column=1, padx=10, pady=5, sticky="w")
        self.entries["cif_display"] = cif_label

    def on_empresa_selected(self, event):
        """✅ IMPLEMENTAR: Callback cuando se selecciona empresa."""
        empresa = self.empresa_frame.combobox.get()
        
        # Manejar empresa no creada
        if empresa == self.session.empresa_no_creada:
            nueva_empresa, nuevo_cif = self.crear_nueva_empresa()
            if nueva_empresa and nuevo_cif:
                self.actualizar_empresas_disponibles()
                self.empresa_frame.combobox.set(nueva_empresa)
                empresa = nueva_empresa
        
        # Actualizar CIF
        if hasattr(self.empresa_frame, 'empresas_dic'):
            cif = self.empresa_frame.empresas_dic.get(empresa, "-")
        else:
            empresas_suasor, empresas_completas = self.session.return_empresas_combo_values(todas=True, create=True)
            cif = empresas_completas.get(empresa, "-")
        
        self.entries["cif_display"].config(text=cif)


    def crear_nueva_empresa(self):
        """✅ IMPLEMENTAR: Crear nueva empresa."""
        from tkinter import simpledialog
        
        # Pedir nombre
        nueva_empresa = simpledialog.askstring("Nueva Empresa", 
                                             "Ingrese el nombre de la nueva empresa:", 
                                             parent=self)
        if not nueva_empresa:
            return None, None
        
        nueva_empresa = nueva_empresa.strip().upper()
        
        # Verificar si existe
        empresas_suasor, empresas_completas = self.session.return_empresas_combo_values(todas=True, create=False)
        if nueva_empresa in empresas_completas.keys():
            cif_existente = empresas_completas[nueva_empresa]
            messagebox.showerror("Error", 
                               f"La empresa '{nueva_empresa}' ya existe con CIF '{cif_existente}'.", 
                               parent=self)
            return None, None
        
        # Pedir CIF
        nuevo_cif = simpledialog.askstring("Número VAT", 
                                         "Ingrese el CIF:", 
                                         parent=self)
        if not nuevo_cif:
            return None, None
        
        nuevo_cif = nuevo_cif.strip().upper()
        
        # Verificar CIF
        if nuevo_cif in empresas_completas.values():
            empresa_existente = [k for k, v in empresas_completas.items() if v == nuevo_cif][0]
            messagebox.showerror("Error", 
                               f"El CIF '{nuevo_cif}' ya existe para '{empresa_existente}'.", 
                               parent=self)
            return None, None
        
        return nueva_empresa, nuevo_cif


    def actualizar_empresas_disponibles(self):
        """✅ IMPLEMENTAR: Actualizar empresas en BusquedaFrame."""
        empresas_suasor, empresas_completas = self.session.return_empresas_combo_values(todas=True, create=True)
        self.empresa_frame.configurar_combobox(empresas_completas, seleccion=None, mostrar=True)



    
    def crear_campo_concepto(self, fila):
        """Campo específico para concepto con combobox."""
        tk.Label(self.content_frame, text="Concepto:", bg="white", font=("Arial", 10, "bold")).grid(
            row=fila, column=0, sticky="w", padx=10, pady=5)
        
        concepto_combobox = ttk.Combobox(self.content_frame, width=40, state="readonly")
        concepto_combobox["values"] = list(self.conceptos_dict.keys())
        concepto_combobox.grid(row=fila, column=1, columnspan=3, padx=10, pady=5, sticky="ew")
        self.entries["concepto"] = concepto_combobox
    
    def crear_campo_descripcion(self, fila):
        """Campo específico para descripción con Text widget."""
        tk.Label(self.content_frame, text="Descripción:", bg="white", font=("Arial", 10, "bold")).grid(
            row=fila, column=0, sticky="nw", padx=10, pady=5)
        
        text_descripcion = tk.Text(self.content_frame, width=40, height=3)
        text_descripcion.grid(row=fila, column=1, columnspan=3, padx=10, pady=5, sticky="ew")
        self.entries["descripcion"] = text_descripcion
    
    def crear_campo_fecha(self, fila):
        """Campo específico para fecha con spinboxes (solo día, mes, año)."""
        tk.Label(self.content_frame, text="Fecha Creación:", bg="white", font=("Arial", 10, "bold")).grid(
            row=fila, column=0, sticky="w", padx=10, pady=5)
        
        date_frame = tk.Frame(self.content_frame, bg="white")
        date_frame.grid(row=fila, column=1, columnspan=3, padx=10, pady=5, sticky="w")
        
        # Día
        tk.Label(date_frame, text="Día:", bg="white").grid(row=0, column=0, padx=2)
        spinbox_dia = tk.Spinbox(date_frame, from_=1, to=31, width=4)
        spinbox_dia.grid(row=0, column=1, padx=2)
        
        # Mes
        tk.Label(date_frame, text="Mes:", bg="white").grid(row=0, column=2, padx=2)
        spinbox_mes = tk.Spinbox(date_frame, from_=1, to=12, width=4)
        spinbox_mes.grid(row=0, column=3, padx=2)
        
        # Año
        tk.Label(date_frame, text="Año:", bg="white").grid(row=0, column=4, padx=2)
        spinbox_anyo = tk.Spinbox(date_frame, from_=1900, to=2100, width=6)
        spinbox_anyo.grid(row=0, column=5, padx=2)
        
        self.entries["dia"] = spinbox_dia
        self.entries["mes"] = spinbox_mes
        self.entries["anyo"] = spinbox_anyo
    
    def crear_campo_tiempo(self, fila):
        """Campo específico para tiempo con spinboxes."""
        tk.Label(self.content_frame, text="Tiempo:", bg="white", font=("Arial", 10, "bold")).grid(
            row=fila, column=0, sticky="w", padx=10, pady=5)
        
        time_frame = tk.Frame(self.content_frame, bg="white")
        time_frame.grid(row=fila, column=1, columnspan=3, padx=10, pady=5, sticky="w")
        
        # Horas
        tk.Label(time_frame, text="Horas:", bg="white").grid(row=0, column=0, padx=2)
        spinbox_horas = tk.Spinbox(time_frame, from_=0, to=23, width=4)
        spinbox_horas.grid(row=0, column=1, padx=2)
        
        # Minutos
        tk.Label(time_frame, text="Minutos:", bg="white").grid(row=0, column=2, padx=2)
        minutos_var = tk.StringVar()
        spinbox_minutos = tk.Spinbox(time_frame, from_=0, to=59, increment=5, width=4, 
                                    textvariable=minutos_var, wrap=True)
        spinbox_minutos.grid(row=0, column=3, padx=2)
        
        def validar_minutos(*args):
            try:
                value = int(minutos_var.get())
                if value >= 60:
                    minutos_var.set("59")
                elif value < 0:
                    minutos_var.set("0")
            except ValueError:
                pass
        
        minutos_var.trace_add("write", validar_minutos)
        
        self.entries["horas"] = spinbox_horas
        self.entries["minutos"] = spinbox_minutos
    
    def crear_campo_texto(self, fila, label, valor="", editable=True):
        """Campo genérico de texto."""
        tk.Label(self.content_frame, text=label, bg="white", font=("Arial", 10, "bold")).grid(
            row=fila, column=0, sticky="w", padx=10, pady=5)
        
        entry = tk.Entry(self.content_frame, width=40)
        if valor:
            entry.insert(0, valor)
        if not editable:
            entry.config(state="disabled")
        entry.grid(row=fila, column=1, columnspan=3, padx=10, pady=5, sticky="ew")
        
        campo_key = label.replace(":", "").lower()
        self.entries[campo_key] = entry
    
    def crear_botones(self):
        """✅ CREA SOLO DOS BOTONES: INSERTAR Y CERRAR."""
        
        # Frame para botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Configurar grid del content_frame
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # ✅ BOTÓN INSERTAR
        btn_insertar = tk.Button(btn_frame, text="✅ Insertar", 
                               command=self.insertar_y_continuar, 
                               bg="#27ae60", fg="white", width=20, height=2,
                               font=("Arial", 11, "bold"))
        btn_insertar.pack(side=tk.LEFT, padx=(0, 10))
        
        # ✅ BOTÓN CERRAR
        btn_cerrar = tk.Button(btn_frame, text="❌ Cerrar", 
                             command=self.cerrar_popup, 
                             bg="#e74c3c", fg="white", width=20, height=2,
                             font=("Arial", 11, "bold"))
        btn_cerrar.pack(side=tk.RIGHT, padx=(10, 0))
    
    def validar_datos(self):
        """✅ VALIDACIÓN CON MENSAJES PERSONALIZADOS."""
        from datetime import datetime
        
        # Validar empresa
        empresa = self.entries["empresa"].get()
        if not empresa or empresa == "":
            messagebox.showerror("Error", "Debe seleccionar una empresa.", parent=self)
            return False
        
        # Validar concepto
        concepto_desc = self.entries["concepto"].get()
        if not empresa.startswith('0') and not concepto_desc:
            if not empresa.startswith('0'):
                messagebox.showerror("Error", "Debe seleccionar un concepto.", parent=self)
                return False
        
        # Validar fecha
        try:
            dia = int(self.entries["dia"].get())
            mes = int(self.entries["mes"].get())
            anyo = int(self.entries["anyo"].get())
            fecha_creacion = datetime(anyo, mes, dia, 0, 0)
        except ValueError:
            messagebox.showerror("Error", "La fecha introducida no es válida.", parent=self)
            return False
        
        # Validar que la fecha no es futura
        if fecha_creacion.date() > datetime.now().date():
            messagebox.showerror("Error", "No se pueden introducir fechas futuras.", parent=self)
            return False
        
        # Validar rango de fecha
        fecha_actual = datetime.now()
        if fecha_actual.month == 1:
            mes_anterior = 12
            anyo_mes_anterior = fecha_actual.year - 1
        else:
            mes_anterior = fecha_actual.month - 1
            anyo_mes_anterior = fecha_actual.year
        
        fecha_limite = datetime(anyo_mes_anterior, mes_anterior, 1).date()
        if fecha_creacion.date() < fecha_limite:
            messagebox.showerror("Error", 
                "Solo se pueden introducir registros con fecha del mes en curso o el anterior.", 
                parent=self)
            return False
        
        # Validar tiempo
        try:
            horas = int(self.entries["horas"].get())
            minutos = int(self.entries["minutos"].get())
            if horas < 0 or minutos < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El tiempo introducido no es válido.", parent=self)
            return False
        
        return True
    
    def obtener_datos(self):
        """Obtiene los datos del formulario."""
        empresa = self.entries["empresa"].get()
        
        # ✅ OBTENER CIF DEL DISPLAY (ya actualizado por el callback)
        cif = self.entries["cif_display"].cget("text")
        if cif == "-":
            cif = ""
        
        concepto_desc = self.entries["concepto"].get()
        concepto_codigo = self.conceptos_dict.get(concepto_desc, "")
        
        descripcion = self.entries["descripcion"].get("1.0", "end-1c")
        
        # Fecha
        dia = int(self.entries["dia"].get())
        mes = int(self.entries["mes"].get())
        anyo = int(self.entries["anyo"].get())
        fecha_creacion = f"{anyo:04d}-{mes:02d}-{dia:02d} 00:00"
        
        # Tiempo en segundos
        horas = int(self.entries["horas"].get())
        minutos = int(self.entries["minutos"].get())
        tiempo_segundos = horas * 3600 + minutos * 60
        
        # ✅ SOLUCIÓN: Manejar correctamente el retorno del método
        resultado = self.session.return_empresas_combo_values(todas=False, create=False)
        if isinstance(resultado, tuple):
            empresas_suasor, _ = resultado
        else:
            empresas_suasor = resultado
        
        vinculada = empresa in empresas_suasor.keys()
        
        return {
            "empresa": empresa,
            "cif": cif,
            "concepto": concepto_codigo,
            "descripcion": descripcion,
            "fecha_creacion": fecha_creacion,
            "tiempo": tiempo_segundos,
            "vinculada": vinculada
        }
    
    def insertar_registro(self):
        """✅ INSERCIÓN CON MENSAJES PERSONALIZADOS."""
        if not self.validar_datos():
            return False
        
        datos = self.obtener_datos()
        
        try:
            query = """
                INSERT INTO registros (tiempo, empresa, concepto, fecha_creacion, state, user, departamento, descripcion, vinculada, cif)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            valores = (
                datos["tiempo"], datos["empresa"], datos["concepto"], 
                datos["fecha_creacion"], "working", self.session.user_id, 
                self.session.department, datos["descripcion"], 
                1 if datos["vinculada"] else 0, datos["cif"]
            )
            
            self.db_manager.cursor.execute(query, valores)
            self.db_manager.conexion.commit()
            
            self.registros_insertados += 1
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al insertar registro:\n{str(e)}", parent=self)
            return False
    
    def insertar_y_continuar(self):
        """✅ INSERTAR CON MENSAJE PERSONALIZADO."""
        if self.insertar_registro():
            messagebox.showinfo("Éxito", 
                f"Registro insertado correctamente.\nTotal insertados: {self.registros_insertados}", 
                parent=self)
            self.resetear_campos()
    
    def resetear_campos(self):
        """Resetea todos los campos a valores por defecto."""
        from datetime import datetime
        
        # ✅ EMPRESA: resetear BusquedaFrame
        self.empresa_frame.combobox.set("Selecciona una empresa")
        self.empresa_frame.buscador_entry.delete(0, tk.END)
        self.entries["cif_display"].config(text="-")
        
        # Concepto en blanco
        self.entries["concepto"].set("")
        
        # Descripción en blanco
        self.entries["descripcion"].delete("1.0", tk.END)
        
        # Fecha actual
        ahora = datetime.now()
        self.entries["dia"].delete(0, tk.END)
        self.entries["dia"].insert(0, str(ahora.day))
        self.entries["mes"].delete(0, tk.END)
        self.entries["mes"].insert(0, str(ahora.month))
        self.entries["anyo"].delete(0, tk.END)
        self.entries["anyo"].insert(0, str(ahora.year))
        
        # Tiempo en 0
        self.entries["horas"].delete(0, tk.END)
        self.entries["horas"].insert(0, "0")
        self.entries["minutos"].delete(0, tk.END)
        self.entries["minutos"].insert(0, "0")
        
        # Focus en empresa
        self.entries["empresa"].focus_set()
    
    def cerrar_popup(self):
        """✅ CIERRA LA VENTANA."""
        if self.winfo_exists():
            self.destroy()
