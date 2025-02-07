import os, json
import pandas as pd
from collections import OrderedDict

CONFIG_FILE = "data/config.json"
DEFAULT_CONFIG = {"session": {"user": "", "pass": ""}}
EMPRESAS_CSV = "data/res_partner.csv"
NUEVAS_EMPRESAS_CSV = "data/new_partners.csv"
EMPLEADOS_CSV = "data/hr_employee.csv"

import os
import json
import pandas as pd

class SessionManager:
    def __init__(self):
        self.empresa_no_creada = '-----❌empresa no creada en SUASOR❌-----'

        self.empleados_l, self.empleados_df = self.load_empleados()
        self.empresas_dic = self.load_empresas_combo_values()

        # Verificar y cargar configuración
        self.config = self.load_config()
        self.user = self.config["session"]["user"]
        resultado = self.empleados_df.loc[self.empleados_df["name"] == self.user, "department_name"]
        self.department = resultado.iloc[0] if not resultado.empty else None  # Si hay resultado, devuelve el primero
        
    @property
    def logged_in(self):
        """Evalúa dinámicamente si el usuario está logueado."""
        return bool(self.user)  # Devuelve True si user no es una cadena vacía

    def load_empleados(self):
        """Carga estática de los empleados."""
        try:
            empleados_df = pd.read_csv(EMPLEADOS_CSV, dtype=str)
            cond1 = empleados_df['department_name'] != "Administration"
            cond2 = empleados_df['department_name'].notna()
            empleados_l = empleados_df.loc[cond1 & cond2, 'name'].tolist()
            return empleados_l, empleados_df
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo en la ruta especificada: {EMPLEADOS_CSV}")
        except Exception as e:
            print(f"Error: {e}")
            return [], pd.DataFrame()


    def load_empresas_combo_values (self):
            nuevas_empresas_df = self.load_new_empresas()
            nuevas_empresas_dic = {row['name'].upper(): row['vat'].upper() for _, row in nuevas_empresas_df.iterrows()}

            empresas_df = self.load_empresas()
            empresas_dic = {row['name'].upper(): row['vat'].upper() for _, row in empresas_df.iterrows()}

            #añadimos el caso de empresa no creada en el diccionario
            no_empresa = self.empresa_no_creada
            cif = '-'

            combo_empresas_dic = OrderedDict([(no_empresa, cif)] + list(nuevas_empresas_dic.items()) + list(empresas_dic.items()))
            return combo_empresas_dic

    def load_new_empresas(self):
        """Carga el archivo de nuevas empresas desde NUEVAS_EMPRESAS_CSV o lo crea vacío si no existe."""
        try:
            if os.path.exists(NUEVAS_EMPRESAS_CSV):
                # Si el archivo existe, cargarlo en un DataFrame
                nuevas_empresas_df = pd.read_csv(
                    NUEVAS_EMPRESAS_CSV,
                    dtype=str,
                    na_values=["", " ", "NaN", "None", "False"],
                    keep_default_na=False
                ).fillna('-')
            else:
                # Si el archivo no existe, crear un DataFrame vacío con las columnas 'name' y 'vat'
                nuevas_empresas_df = pd.DataFrame(columns=['name', 'vat'])
                
                # Guardar el DataFrame vacío en el archivo para futuras referencias
                nuevas_empresas_df.to_csv(NUEVAS_EMPRESAS_CSV, index=False)
                print(f"Se creó un archivo vacío en: {NUEVAS_EMPRESAS_CSV}")
            
            return nuevas_empresas_df
        except Exception as e:
            print(f"Error al cargar o crear el archivo de empleados: {e}")
            return pd.DataFrame(columns=['name', 'vat'])    
        

    def load_empresas(self):
        """Carga estática del listado de empresas."""
        try:
            empresas_df = pd.read_csv(
                EMPRESAS_CSV, 
                dtype=str, 
                na_values=["", " ", "NaN", "None", "False"], 
                keep_default_na=False
            ).fillna('-')
            
            return empresas_df
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo en la ruta especificada: {EMPRESAS_CSV}")
        except Exception as e:
            print(f"Error: {e}")
            return {}, pd.DataFrame()

    def load_config(self):
        """Carga el archivo de configuración o lo crea si no existe."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as file:
                    return json.load(file)
            else:
                return self._crear_config_predeterminado()
        except json.JSONDecodeError:
            print("Error: El archivo de configuración está corrupto. Se restaurará uno nuevo.")
            return self._crear_config_predeterminado()
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
            return DEFAULT_CONFIG

    def _crear_config_predeterminado(self):
        """Crea un archivo de configuración predeterminado."""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as file:
                json.dump(DEFAULT_CONFIG, file, indent=4)
            return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error al crear el archivo de configuración: {e}")
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

