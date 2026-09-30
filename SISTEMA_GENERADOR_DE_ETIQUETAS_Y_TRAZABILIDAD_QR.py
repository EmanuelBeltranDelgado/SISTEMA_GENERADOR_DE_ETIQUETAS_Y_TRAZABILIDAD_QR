"""
==============================================================================
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣧⣼⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⣀⣀⣀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⣀⣀⣀⡀⠀⠀⠀
⠀⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⠀
⠀⣙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣋⠀
⣿⣿⣿⣿⣿⣿⣿⠁⠀⠈⠻⠿⠀⠀⠿⠟⠁⠀⠈⣿⣿⣿⣿⣿⣿⣿
⠘⢿⣿⣿⣿⣿⣿⣦⣤⣤⣄⡀⠀⠀⢀⣠⣤⣤⣴⣿⣿⣿⣿⣿⡿⠋
⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⠿⠋⠀⣠⣄⠀⠙⠿⣿⣿⣿⣿⣿⡿⠋⠀⠀
⠀⠀⠀⢰⣿⣿⣿⣿⣿⠀⠀⢠⣿⣿⡄⠀⠀⣿⣿⣿⣿⣿⡆⠀⠀⠀
⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣾⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀
⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀
⠀⠀⠀⠈⠛⠛⣿⣿⣿⣿⣿⡿⠛⠛⢿⣿⣿⣿⣿⣿⠛⠛⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠘⠛⠛⠉⠁⠀⠀⠀⠀⠈⠉⠛⠛⠃⠀⠀⠀⠀⠀⠀
==============================================================================
  NOMBRE/PROYECTO : SISTEMA GENERADOR DE ETIQUETAS Y TRAZABILIDAD QR
  DESARROLLADOR   : [Emanuel Beltran Delgado / Medusa Electronic S.A de C.V]
  VERSIÓN         : 1.2.4
  FECHA CREACIÓN  : [30/09/2026]
  FOLIO           : SWM-2026-0003
  DESCRIPCIÓN     : Sistema con interfaz gráfica conectada a una base de datos PostgreSQL.
                    Genera etiquetas con QR para recepción de material, Producto terminado y PCB.
==============================================================================
"""

"""
===============================================================================
SISTEMA DE GESTIÓN DE ETIQUETAS Y TRAZABILIDAD QR - MEDUSA ELECTRONIC
===============================================================================
MÓDULOS PRINCIPALES:
1. Recepción de Materiales: Generación e impresión de etiquetas con código QR.
2. Consulta e Inventario de etiquetas_recepcion: Filtrado, descuento/consumo de stock y cambio de ubicación.
3. Producto Terminado (PT): Generación y consulta de etiquetas de entrega/embarque.
4. Trazabilidad QR PCB: Generación masiva y consecutiva de seriales numéricos.
5. Trazabilidad QR M-G-S: Registro y control de muestras (Master, Golden, Silver).

REQUISITOS PREVIOS (Librerías requeridas):
  pip install psycopg2-binary pillow qrcode reportlab python-dotenv
===============================================================================
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from config.database import init_db
from views.styles import setup_styles
from views.tab_recepcion import TabRecepcion
from views.tab_producto_terminado import TabProductoTerminado
from views.tab_trazabilidad_pcb import TabTrazabilidadPCB
from views.tab_trazabilidad_gms import TabTrazabilidadGMS


# =============================================================================
# --- APLICACIÓN PRINCIPAL DE INTERFAZ GRÁFICA (TKINTER) ---
# =============================================================================
class AplicacionMedusaEtiquetasQR:
    def __init__(self, root):
        """
        Inicializador de la ventana principal y gestor del ciclo de vida de la UI.
        """
        self.root = root
        self.root.title("SISTEMA GENERADOR DE ETIQUETAS Y TRAZABILIDAD_QR")
        self.root.geometry("1920x1080")
        self.root.state('zoomed') # Iniciar maximizado en sistemas Windows
        self.root.configure(bg="#f4f6f8")

        # Carga del ícono (.ico)
        dir_script = Path(__file__).resolve().parent
        ruta_icono = dir_script / "SistemaTrazabilidad.ico"
        if ruta_icono.exists():
            try:
                self.root.iconbitmap(ruta_icono)
            except Exception as e:
                print(f"Error al cargar el icono .ico: {e}")

        # Configuración de estilos visuales ttk
        self.style = setup_styles(self.root)

        header_frame = ttk.Frame(self.root, padding=(10, 10, 10, 5))
        header_frame.pack(side=tk.TOP, fill=tk.X)

        # Configuramos 3 columnas: la 0 (logo) y la 2 (espaciador simétrico) se ajustan, la 1 (título) queda al centro
        header_frame.columnconfigure(0, weight=0)
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=0)

        ruta_logo = dir_script / "Medusa_Logo_Sin_Fondo.png"
        if ruta_logo.exists():
            try:
                logo_img = Image.open(ruta_logo).convert("RGBA")
                logo_img.thumbnail((220, 60), Image.Resampling.LANCZOS)
                self.logo_app_tk = ImageTk.PhotoImage(logo_img)
                lbl_logo_app = ttk.Label(header_frame, image=self.logo_app_tk)
                lbl_logo_app.grid(row=0, column=0, sticky="w")
            except Exception as e:
                print(f"Error al cargar logo: {e}")

        lbl_titulo_app = ttk.Label(
            header_frame, 
            text="SISTEMA GENERADOR DE ETIQUETAS Y TRAZABILIDAD_QR", 
            font=("Segoe UI", 14, "bold"),
            foreground="#2c3e50"
        )
        # Se coloca en la columna central (1)
        lbl_titulo_app.grid(row=0, column=1, sticky="n")

        # ---------------------------------------------------------------------
        # CONTENEDOR DE PESTAÑAS (Notebook)
        # ---------------------------------------------------------------------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        # Creación de pestañas individuales
        tab_generar = ttk.Frame(self.notebook, style="TFrame")
        tab_consultar = ttk.Frame(self.notebook, style="TFrame")
        tab_pt_generar = ttk.Frame(self.notebook, style="TFrame")
        tab_pt_consultar = ttk.Frame(self.notebook, style="TFrame")
        tab_pc_generar = ttk.Frame(self.notebook, style="TFrame")
        tab_pc_consultar = ttk.Frame(self.notebook, style="TFrame")
        tab_gms_generar = ttk.Frame(self.notebook, style="TFrame")
        tab_gms_consultar = ttk.Frame(self.notebook, style="TFrame")

        # Registro de pestañas en el Notebook
        self.notebook.add(tab_generar, text="Generar etiquetas de recepción")
        self.notebook.add(tab_consultar, text="Buscar etiquetas recepción")
        self.notebook.add(tab_pt_generar, text="Generar etiqueta Producto Terminado")
        self.notebook.add(tab_pt_consultar, text="Buscar etiquetas Producto Terminado")
        self.notebook.add(tab_pc_generar, text="Trazabilidad QR PCB")
        self.notebook.add(tab_pc_consultar, text="Buscar QR PCB")
        self.notebook.add(tab_gms_generar, text="Trazabilidad QR M-G-S")
        self.notebook.add(tab_gms_consultar, text="Buscar QR M-G-S")

        # Instanciación modular de controladores de vistas/pestañas
        self.mod_recepcion = TabRecepcion(self, tab_generar, tab_consultar)
        self.mod_pt = TabProductoTerminado(self, tab_pt_generar, tab_pt_consultar)
        self.mod_pcb = TabTrazabilidadPCB(self, tab_pc_generar, tab_pc_consultar)
        self.mod_gms = TabTrazabilidadGMS(self, tab_gms_generar, tab_gms_consultar)


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = AplicacionMedusaEtiquetasQR(root)
    root.mainloop()