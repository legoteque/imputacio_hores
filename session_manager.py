import os, json
from collections import OrderedDict
from functions import CONFIG_FILE, DEFAULT_CONFIG


import os
import json
import pandas as pd

class SessionManager:
    def __init__(self, app):
        self.app = app
        self.empresa_no_creada = '-----❌empresa no creada en SUASOR❌-----'

        self.empleados_l, self.empleados_df = self.app.db_manager.load_empleados_sqlite()
        print ("self.empleados_df", self.empleados_df)
        # Verificar y cargar configuración
        self.config = self.load_config()
        self.user = self.config["session"]["user"]
        resultado = self.empleados_df.loc[self.empleados_df["name"] == self.user, "department_name"]
        self.department = resultado.iloc[0] if not resultado.empty else None  # Si hay resultado, devuelve el primero


    @property
    def logged_in(self):
        """Evalúa dinámicamente si el usuario está logueado."""
        return bool(self.user)  # Devuelve True si user no es una cadena vacía


    def return_empresas_combo_values(self, todas=True, create=True): 
        nuevas_empresas_dic = self.app.db_manager.obtener_empresas_temporales()
        empresas_df = self.app.db_manager.load_empresas_sqlite()
        empresas_dic = {row['name'].upper(): row['vat'].upper() for _, row in empresas_df.iterrows()}

        # Diccionario base con empresas existentes
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
        
       
    def load_config(self):
        """Carga el archivo de configuración o lo crea si no existe."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as file:
                    return json.load(file)
            else:
                return self._crear_config_predeterminado()
        except json.JSONDecodeError:
            #print("Error: El archivo de configuración está corrupto. Se restaurará uno nuevo.")
            return self._crear_config_predeterminado()
        except Exception as e:
            #print(f"Error al cargar la configuración: {e}")
            return DEFAULT_CONFIG

    def _crear_config_predeterminado(self):
        """Crea un archivo de configuración predeterminado."""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as file:
                json.dump(DEFAULT_CONFIG, file, indent=4)
            return DEFAULT_CONFIG
        except Exception as e:
            #print(f"Error al crear el archivo de configuración: {e}")
            return DEFAULT_CONFIG


    def write_config(self, user):
        """Guarda el usuario en la configuración."""
        self.config["session"]["user"] = user
        with open(CONFIG_FILE, "w") as file:
            json.dump(self.config, file, indent=4)

    def selected_user(self, user):
        """Selecciona un usuario y lo guarda en la configuración."""
        self.write_config(user)
        self.user = self.config["session"]["user"]
        resultado = self.empleados_df.loc[self.empleados_df["name"] == self.user, "department_name"]
        self.department = resultado.iloc[0] if not resultado.empty else None  # Si hay resultado, devuelve el primero


    def unselected_user(self):
        """Desconecta al usuario."""
        self.write_config("")
        self.user = ""

