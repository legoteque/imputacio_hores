import tkinter as tk
from tkinter import ttk

def seleccionar(event):
    seleccion = listbox.get(listbox.curselection())
    combo_var.set(seleccion)
    top.destroy()  # Cierra la ventana emergente

def abrir_lista():
    global top, listbox
    top = tk.Toplevel(root)
    top.geometry("200x150")
    listbox = tk.Listbox(top)

    colores = [("Rojo", "red"), ("Verde", "green"), ("Azul", "blue"), ("Amarillo", "yellow")]
    
    for i, (texto, color) in enumerate(colores):
        listbox.insert(i, texto)
        listbox.itemconfig(i, fg=color)  # Aplica el color al texto

    listbox.pack(expand=True, fill="both")
    listbox.bind("<<ListboxSelect>>", seleccionar)

root = tk.Tk()
combo_var = tk.StringVar()
entry = ttk.Entry(root, textvariable=combo_var, state="readonly")
entry.pack(pady=10)
btn = ttk.Button(root, text="Seleccionar", command=abrir_lista)
btn.pack(pady=5)

root.mainloop()
