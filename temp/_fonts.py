import tkinter as tk
from tkinter import ttk

def cambiar_fuente(fuente):
    timer_label.config(font=(fuente, 32, "bold"))

# Lista de fuentes digitales a probar
fuentes = ["DS-Digital", "Digital-7", "LCD", "Seven Segment", "Bahnschrift", "Consolas", "Courier New", "OCR A Extended"]

# Crear ventana
root = tk.Tk()
root.title("Prueba de Fuentes")

# Etiqueta con cronómetro
timer_label = ttk.Label(root, text="12:34:56", font=("DS-Digital", 32, "bold"))
timer_label.pack(pady=20, padx=20)

# Menú desplegable para cambiar fuente
fuente_var = tk.StringVar(value="DS-Digital")
fuente_menu = ttk.Combobox(root, textvariable=fuente_var, values=fuentes)
fuente_menu.pack(pady=10)
fuente_menu.bind("<<ComboboxSelected>>", lambda event: cambiar_fuente(fuente_var.get()))

root.mainloop()

# import tkinter as tk
# from tkinter import font

# root = tk.Tk()
# fuentes_disponibles = list(font.families())
# root.destroy()

# # Imprimir fuentes en la consola
# for fuente in sorted(fuentes_disponibles):
#     print(fuente)