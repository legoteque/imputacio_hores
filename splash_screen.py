import tkinter as tk
from tkinter import ttk

class SplashFrame:
    def __init__(self, root):
        self.root = root
        
        # Crear frame de splash que ocupe toda la ventana
        self.splash_frame = tk.Frame(root, bg="#34495e")
        self.splash_frame.pack(fill="both", expand=True)
        
        # Contenido del splash
        tk.Label(self.splash_frame, text="In Extenso. Imputaciones", 
                font=("Arial", 14, "bold"), bg="#34495e", fg="white").pack(pady=(50, 10))
        
        self.status_label = tk.Label(self.splash_frame, text="Iniciando aplicación...", 
                                   font=("Arial", 10), bg="#34495e", fg="#bdc3c7")
        self.status_label.pack(pady=(5, 10))
        
        # Barra de progreso
        self.progress = ttk.Progressbar(self.splash_frame, length=300, mode='determinate')
        self.progress.pack(pady=(10, 50))
        self.progress['value'] = 0
        
    def update_message(self, message):
        try:
            self.status_label.config(text=message)
            self.root.update()
        except tk.TclError:
            pass
    
    def update_progress(self, value):
        try:
            self.progress['value'] = value
            self.root.update()
        except tk.TclError:
            pass
    
    def destroy_splash(self):
        try:
            self.splash_frame.destroy()
        except tk.TclError:
            pass