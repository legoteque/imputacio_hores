import tkinter as tk
from tkinter import ttk

class SplashScreen:
    def __init__(self, root):
        self.top = tk.Toplevel(root)
        self.top.title("Cargando aplicación...")
        self.top.geometry("400x150")
        self.top.overrideredirect(True)       # Quita bordes y barra de título
        self.top.attributes("-topmost", True)  # Mantener siempre al frente

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(self.top, orient="horizontal", length=300,
                                        mode="determinate", maximum=100,
                                        variable=self.progress_var)
        self.progress.pack(pady=10)

        self.status_label = tk.Label(self.top, text="Iniciando...", font=("Calibri", 12))
        self.status_label.pack(pady=5)
        self.top.update()

    def update_message(self, message):
        self.status_label.config(text=message)
        self.top.update()

    def update_progress(self, value):
        self.progress_var.set(value)
        self.top.update()

    def destroy(self):
        self.top.destroy()