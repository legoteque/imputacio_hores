import os, json
from collections import OrderedDict
from functions import CONFIG_FILE, DEFAULT_CONFIG
from functions import CustomMessageBox as messagebox


import os
import json
import pandas as pd

class SessionManager:
    def __init__(self, app):
        self.app = app
        self.empresa_no_creada = '-----❌empresa no creada en SUASOR❌-----'

        #quan entrem carrega les taules de empleados y empresas del sqlserver al sqlite
        self.app.db_manager.sincronizar_empleados()
        self.app.db_manager.sincronizar_empresas()
        self.app.db_manager.sincronizar_conceptos()

        #extraiem la informacio del sqlite
        self.empleados_dict, self.empleados_df = self.app.db_manager.load_empleados_sqlite()
        # Verificar y cargar configuración
        self.config = self.load_config()
        self.user_id = self.config["session"]["id"]

        # Buscamos la fila cuyo id coincida con self.user_id
        mask = self.empleados_df["id"] == self.user_id
        if mask.any():
            # Tomamos la primera fila coincidente
            fila = self.empleados_df.loc[mask, ["name","department_name"]].iloc[0]
            self.user = fila['name']
            self.department = fila["department_name"]
        else:
            # Si no hay coincidencias, vaciamos self.user y ponemos None en department
            self.user = ""
            self.department = None


    @property
    def logged_in(self):
        """Evalúa dinámicamente si el usuario está logueado."""
        return bool(self.user)  # Devuelve True si user no es una cadena vacía


    def return_empresas_combo_values(self, todas=True, create=True): 
        nuevas_empresas_dic = self.app.db_manager.obtener_empresas_temporales()
        empresas_df = self.app.db_manager.load_empresas_sqlite()
        empresas_dic = {row['name'].upper(): row['vat'].upper() for _, row in empresas_df.iterrows()}

        # Diccionario base ordenado con empresas existentes
        combo_empresas_dic = OrderedDict()

        # Si create=True, se añade la opción "empresa no creada"
        if create:
            no_empresa = self.empresa_no_creada
            cif = '-'
            combo_empresas_dic[no_empresa] = cif

        # Si todas=True, se añaden las nuevas empresas para devolver las de suasor y las nuevas
        if todas:
            combo_empresas_dic.update(nuevas_empresas_dic)

        # Siempre se añaden las empresas existentes
        combo_empresas_dic.update(empresas_dic)

        if todas:
            return empresas_dic, combo_empresas_dic
        else:
            return empresas_dic
        
    def return_conceptos_combo_values(self):
        """Devuelve un diccionario con los conceptos del departamento del usuario."""
        try:
            conceptos_df = self.app.db_manager.load_conceptos_sqlite()
            if conceptos_df.empty:
                return {}
            
            # Crear diccionario {Descripcion: Cod_concepto}
            conceptos_dict = dict(zip(conceptos_df['Descripcion'], conceptos_df['Cod_ concepto']))
            return conceptos_dict
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar conceptos:\n{e}")
            return {}


    def load_config(self):
        """Carga el archivo de configuración o lo crea si no existe.
        Si detecta formato antiguo, crea uno nuevo predeterminado."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as file:
                    config_data = json.load(file)
                    
                # Verificar si es formato antiguo (tiene "user" en lugar de "id")
                if "version" not in config_data:
                    messagebox.showinfo("Configuración Actualizada", 
                                    "Se ha detectado una configuración de versión anterior.\n\n"
                                    "Se creará una nueva configuración compatible.\n"
                                    "Deberá seleccionar su usuario nuevamente.")
                    
                    self._crear_config_predeterminado()
                    self.app.db_manager.sqlite_update_to_new_version()
                    return DEFAULT_CONFIG
                
                # Si está en formato correcto, devolverlo
                return config_data
            else:
                return self._crear_config_predeterminado()
                
        except json.JSONDecodeError:
            messagebox.showerror("Error de Configuración", 
                                "El archivo de configuración está corrupto.\n\n"
                                "Se creará una nueva configuración predeterminada.")
            return self._crear_config_predeterminado()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar la configuración:\n{e}")
            return DEFAULT_CONFIG

    def _crear_config_predeterminado(self):
        """Crea un archivo de configuración predeterminado."""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as file:
                json.dump(DEFAULT_CONFIG, file, indent=4)
            return DEFAULT_CONFIG
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear el archivo de configuración:\n{e}")
            return DEFAULT_CONFIG


    def write_config(self, user_id):
        """Guarda el usuario en la configuración."""
        self.config["session"]["id"] = user_id
        with open(CONFIG_FILE, "w") as file:
            json.dump(self.config, file, indent=4)

    def selected_user(self, user_id, name):
        """Selecciona un usuario y lo guarda en la configuración."""
        self.write_config(user_id)
        self.user_id = self.config["session"]["id"]
        self.user = name
        resultado = self.empleados_df.loc[self.empleados_df["id"] == self.user_id, "department_name"]
        self.department = resultado.iloc[0] if not resultado.empty else None  # Si hay resultado, devuelve el primero


    def unselected_user(self):
        """Desconecta al usuario."""
        self.write_config("")
        self.user = ""



    def actualizar_datos_desde_servidor(self):
        """
        Actualiza los datos (empleados, empresas y conceptos) desde SQL Server al SQLite
        y recarga los datos en la aplicación.
        
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        
        # Verificar que hay conexión con SQL Server
        if not self.app.sql_server_manager.conectado:
            messagebox.showerror("Sin conexión", 
                            "No hay conexión disponible con SQL Server.\n"
                            "Verifique la conectividad de red.")
            return False
        
        try:
            # 1. Sincronizar empleados
            empleados_ok = self.app.db_manager.sincronizar_empleados()
            
            # 2. Sincronizar empresas  
            empresas_ok = self.app.db_manager.sincronizar_empresas()
            
            # 3. Sincronizar conceptos
            conceptos_ok = self.app.db_manager.sincronizar_conceptos()
            
            # 4. Actualizar datos en la aplicación (solo si el usuario está logueado)
            if self.logged_in:
                # Recargar empleados en memoria
                if empleados_ok:
                    self.empleados_dict, self.empleados_df = self.app.db_manager.load_empleados_sqlite()
                
                # Recargar empresas y conceptos en la app (comboboxes)
                if empresas_ok or conceptos_ok:
                    self.app.reload_empresas_combobox_update()
            
            # 5. Verificar si todo fue exitoso
            if empleados_ok and empresas_ok and conceptos_ok:
                messagebox.showinfo("Actualización exitosa", 
                                "Los datos han sido actualizados correctamente desde el servidor.")
                return True
            else:
                messagebox.showerror("Error en actualización", 
                                "No se pudieron actualizar todos los datos.\n"
                                "Algunos datos pueden no estar actualizados.")
                return False
                
        except Exception as e:
            messagebox.showerror("Error de actualización", 
                            f"Error durante la actualización de datos:\n{str(e)}")
            return False


