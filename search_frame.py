import tkinter as tk
from tkinter import ttk
from functions import COLORES

class BusquedaFrame(tk.Frame):
    def __init__(self, parent, session, label_text="Filtro:", callback=None):
        super().__init__(parent, bg=COLORES["rojo_oscuro"], bd=2, relief="ridge")
        self.session = session
        self.callback = callback
        self.empresas_dic = {}

        # Etiqueta de filtro
        ttk.Label(self, text=label_text, style="TLabel").pack(side="left", padx=5)
        
        # Campo de búsqueda
        self.buscador_entry = ttk.Entry(self, width=20, style="TEntry")
        self.buscador_entry.pack(side="left", padx=5, pady=5)

        self.combobox = ttk.Combobox(self, style="TCombobox", state="readonly")
        self.combobox.pack(side="left", expand=True, fill="x", padx=5, pady=5)
        
        # Eventos
        self.buscador_entry.bind("<KeyRelease>", self.filter_combobox)
        self.combobox.bind("<<ComboboxSelected>>", self.on_selection)


    def filter_combobox(self, event):
        search_text = self.buscador_entry.get().lower().strip()
        if not search_text:
            valores = list(self.empresas_dic.keys())
        else:
            words = search_text.split()
            valores = [name for name, cif in self.empresas_dic.items()
                       if all(word in name.lower() or (cif and word in cif.lower()) for word in words)]

        if self.session.empresa_no_creada in valores:
            valores.remove(self.session.empresa_no_creada)
        valores.append(self.session.empresa_no_creada)

        self.combobox["values"] = valores
        if valores:
            self.combobox.current(0)


    def configurar_combobox(self, empresas_dic, seleccion=None, mostrar=True):
        """Muestra/oculta el combobox y configura sus valores y selección si se proporcionan."""
        self.empresas_dic = empresas_dic
        valores = list(self.empresas_dic.keys())
                       
        if mostrar:
            self.combobox.pack(fill="x", padx=5, pady=5)
            if valores is not None:
                self.combobox["values"] = valores
            if seleccion is not None:
                self.combobox.set(seleccion)
        else:
            self.combobox.pack_forget()

    
    def habilitar_seleccion(self, enable=True):
        """
        Habilita o deshabilita los eventos del Combobox.
        Parámetros: enable (bool): Si es True, habilita los eventos; si es False, los deshabilita.
        """
        if enable:
            self.combobox.bind("<<ComboboxSelected>>", self.on_selection)
        else:
            self.combobox.unbind("<<ComboboxSelected>>")


    def on_selection(self, event):
        if self.callback:
            self.callback(self.combobox.get())
