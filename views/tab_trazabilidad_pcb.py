"""
===============================================================================
MÓDULO PESTAÑAS: TRAZABILIDAD QR PCB
===============================================================================
Generación masiva y serializada consecutiva de códigos QR ultracompactos (40x15 mm)
para tarjetas electrónicas/PCB, gestión de consultas y exportación masiva.
===============================================================================
"""

import os
from pathlib import Path
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from psycopg2 import sql

from config.database import get_db_connection
from utils.qr_generator import QRGenerator
from utils.validators import es_entero_valido

class TabTrazabilidadPCB:
    def __init__(self, main_app, tab_generar, tab_consultar):
        self.main_app = main_app
        self.root = main_app.root
        self.tab_pc_generar = tab_generar
        self.tab_pc_consultar = tab_consultar

        # ---------------------------------------------------------------------
        # VARIABLES DE CONTROL DE TKINTER (Módulo: Trazabilidad QR PCB)
        # ---------------------------------------------------------------------
        self.var_pc_work_order = tk.StringVar(value="")
        self.var_pc_pn = tk.StringVar(value="")
        self.var_pc_lote = tk.StringVar(value="")
        self.var_pc_fecha = tk.StringVar(value=datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_pc_num_etiquetas = tk.StringVar(value="1")
        self.var_pc_select_all = tk.BooleanVar(value=False)

        self.img_pc_etiqueta_pil = None

        # Inicializar UI
        self.setup_tab_pc_generar()
        self.setup_tab_pc_consultar()

    # =========================================================================
    # --- MÓDULO 4: TRAZABILIDAD QR PCB (SERIALIZACIÓN MASIVA) ---
    # =========================================================================
    def obtener_siguiente_serial_pc(self):
        """
        Consulta la base de datos para obtener el último serial numérico registrado y 
        retorna el consecutivo formateado a 9 dígitos rellenos con ceros (ej. '000000005').
        """
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT serial FROM etiqueta_trazabilidad_qr_pcb ORDER BY id DESC LIMIT 1;")
                    last_serial = cur.fetchone()
                    if last_serial and last_serial[0] and last_serial[0].isdigit():
                        num = int(last_serial[0]) + 1
                    else:
                        num = 1
                    return f"{num:09d}"
            finally:
                conn.close()
        return "000000001"

    def setup_tab_pc_generar(self):
        """UI para la autogeneración de etiquetas serie para PCBs/Tarjetas Electrónicas."""
        panel_izq = ttk.Frame(self.tab_pc_generar, padding=15)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(panel_izq, text="Datos Trazabilidad QR PCB", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        vcmd_num = (self.root.register(es_entero_valido), '%P')

        fields = [
            ("Work Order *", self.var_pc_work_order),
            ("P/N *", self.var_pc_pn),
            ("Lote *", self.var_pc_lote),
            ("Fecha *", self.var_pc_fecha),
        ]

        row = 1
        for label_text, var in fields:
            ttk.Label(panel_izq, text=label_text).grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(panel_izq, textvariable=var, width=28).grid(row=row, column=1, sticky="w", pady=5, padx=(5, 0))
            row += 1

        ttk.Label(panel_izq, text="Cantidad de etiquetas *").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(panel_izq, textvariable=self.var_pc_num_etiquetas, width=28, validate="key", validatecommand=vcmd_num).grid(row=row, column=1, sticky="w", pady=5, padx=(5, 0))
        row += 1

        frame_botones = ttk.Frame(panel_izq)
        frame_botones.grid(row=row, column=0, columnspan=2, pady=20, sticky="ew")

        btn_generar = ttk.Button(frame_botones, text="GENERAR ETIQUETAS", style="Primary.TButton", command=self.accion_generar_etiqueta_pc)
        btn_generar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_limpiar = ttk.Button(frame_botones, text="LIMPIAR CAMPOS", style="Secondary.TButton", command=self.limpiar_campos_pc)
        btn_limpiar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        panel_der = ttk.Frame(self.tab_pc_generar, padding=15)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.card_pc_preview = tk.Frame(panel_der, bg="#f0f0f0", bd=1, relief="solid", highlightthickness=1, highlightbackground="#dcdfe6")
        self.card_pc_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        lbl_titulo_preview = tk.Label(self.card_pc_preview, text="Vista previa 40 × 15 mm", font=("Segoe UI", 9), bg="#f0f0f0", fg="#333333")
        lbl_titulo_preview.pack(anchor="nw", padx=8, pady=8)

        self.lbl_pc_preview = tk.Label(self.card_pc_preview, text="Captura los datos y pulsa GENERAR ETIQUETA", font=("Segoe UI", 10), bg="#f0f0f0", fg="#000000")
        self.lbl_pc_preview.pack(anchor="center", expand=True)

    def render_etiqueta_pc(self, datos):
        """Renderiza una etiqueta ultra-compacta (40x15 mm) optimizada para PCB."""
        width, height = 400, 150
        img = Image.new('RGB', (width, height), color='white')
        d = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arialbd.ttf", 20)
        except:
            font_title = ImageFont.load_default()

        serial_val = datos.get('serial', '')
        if str(serial_val).isdigit():
            serial_str = f"{int(serial_val):09d}"
        else:
            serial_str = str(serial_val)

        qr_content = f"SERIAL-{serial_str}  WO-{datos.get('work_order', '')}  PN-{datos.get('pn', '')}  LOTE-{datos.get('lote', '')}"
        qr_img = QRGenerator.make(qr_content, box_size=8)
        qr_img = qr_img.resize((120, 120), Image.Resampling.NEAREST)
        img.paste(qr_img, (width - 135, 15))

        text_str = f"Serial: {serial_str}"
        d.text((15, (height // 2) - 12), text_str, fill='black', font=font_title)

        return img

    def accion_generar_etiqueta_pc(self):
        """Genera iterativamente un bloque masivo de seriales consecutivos en DB."""
        wo = self.var_pc_work_order.get().strip()
        pn = self.var_pc_pn.get().strip()
        lote = self.var_pc_lote.get().strip()
        fecha = self.var_pc_fecha.get().strip()
        num_etiq_str = self.var_pc_num_etiquetas.get().strip()

        if not all([wo, pn, lote, fecha, num_etiq_str]):
            messagebox.showwarning("Campos Incompletos", "Work Order, P/N, Lote, Fecha y Cantidad de etiquetas son obligatorios.")
            return

        num_etiquetas = int(num_etiq_str)
        if num_etiquetas < 1:
            messagebox.showwarning("Valor Inválido", "El número de etiquetas debe ser al menos 1.")
            return

        serial_inicial = self.obtener_siguiente_serial_pc()

        datos_preview = {
            'serial': serial_inicial,
            'work_order': wo,
            'pn': pn,
            'lote': lote,
            'cantidad': str(num_etiquetas),
            'fecha': fecha
        }

        self.img_pc_etiqueta_pil = self.render_etiqueta_pc(datos_preview)
        img_tk = ImageTk.PhotoImage(self.img_pc_etiqueta_pil.resize((360, 135)))
        self.lbl_pc_preview.config(image=img_tk)
        self.lbl_pc_preview.image = img_tk

        confirm = messagebox.askyesno("Confirmar Generación", f"Se generarán {num_etiquetas} seriales consecutivos a partir de: {serial_inicial}\n\n¿Desea guardarlos en la base de datos?")
        
        if confirm:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        actual_num = int(serial_inicial)
                        for i in range(num_etiquetas):
                            ser_str = f"{actual_num + i:09d}"
                            cur.execute("""
                                INSERT INTO etiqueta_trazabilidad_qr_pcb (serial, work_order, pn, lote, cantidad, fecha)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (ser_str, wo, pn, lote, str(num_etiquetas), fecha))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Se registraron {num_etiquetas} etiquetas correctamente.")
                    self.buscar_registros_pc()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudieron registrar las etiquetas:\n{e}")
                finally:
                    conn.close()

    def limpiar_campos_pc(self):
        """Limpia los controles de entrada del módulo PCB."""
        self.var_pc_work_order.set("")
        self.var_pc_pn.set("")
        self.var_pc_lote.set("")
        self.var_pc_fecha.set(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_pc_num_etiquetas.set("1")
        self.lbl_pc_preview.config(image="", text="Captura los datos y pulsa GENERAR ETIQUETA")
        self.lbl_pc_preview.image = None

    def setup_tab_pc_consultar(self):
        """Construye la UI para consulta y exportación matricial/en rejilla de etiquetas PCB."""
        panel_top = ttk.Frame(self.tab_pc_consultar, padding=10)
        panel_top.pack(fill=tk.X)

        ttk.Label(panel_top, text="Buscar por:").pack(side=tk.LEFT, padx=5)
        
        self.combo_pc_criterio = ttk.Combobox(panel_top, state="readonly", values=[
            "Todos", "Serial", "Work Order", "P/N", "Lote", "Cantidad", "Fecha"
        ])
        self.combo_pc_criterio.current(0)
        self.combo_pc_criterio.pack(side=tk.LEFT, padx=5)

        self.var_pc_busqueda = tk.StringVar()
        ttk.Entry(panel_top, textvariable=self.var_pc_busqueda, width=25).pack(side=tk.LEFT, padx=5)

        btn_buscar = ttk.Button(panel_top, text="Buscar", style="Primary.TButton", command=self.buscar_registros_pc)
        btn_buscar.pack(side=tk.LEFT, padx=5)

        chk_all = ttk.Checkbutton(
            panel_top, 
            text="Seleccionar Todo", 
            variable=self.var_pc_select_all, 
            command=self.toggle_seleccionar_todo_pc
        )
        chk_all.pack(side=tk.RIGHT, padx=10)

        columns = ("db_id", "serial", "work_order", "pn", "lote", "cantidad", "fecha")
        self.tree_pc = ttk.Treeview(self.tab_pc_consultar, columns=columns, show="headings", selectmode="extended", height=12)
        
        self.tree_pc.configure(displaycolumns=("serial", "work_order", "pn", "lote", "fecha"))

        self.tree_pc.heading("serial", text="Serial QR")
        self.tree_pc.heading("work_order", text="Work Order")
        self.tree_pc.heading("pn", text="P/N")
        self.tree_pc.heading("lote", text="Lote")
        self.tree_pc.heading("fecha", text="Fecha")

        self.tree_pc.column("serial", width=120)
        self.tree_pc.column("work_order", width=120)
        self.tree_pc.column("pn", width=120)
        self.tree_pc.column("lote", width=100)
        self.tree_pc.column("fecha", width=100)

        self.tree_pc.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree_pc.bind("<Double-1>", lambda event: self.mostrar_popup_etiqueta_pc())

        panel_acciones = ttk.Frame(self.tab_pc_consultar, padding=10)
        panel_acciones.pack(fill=tk.X)

        ttk.Button(panel_acciones, text="Ver Etiqueta", style="Primary.TButton", command=self.mostrar_popup_etiqueta_pc).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Exportar Seleccionados (PNG)", style="Secondary.TButton", command=self.exportar_png_multiples_pc).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Exportar Seleccionados (PDF)", style="Secondary.TButton", command=self.exportar_pdf_multiples_pc).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Eliminar Seleccionados", style="Danger.TButton", command=self.eliminar_registro_pc).pack(side=tk.RIGHT, padx=5)

        self.buscar_registros_pc()

    def toggle_seleccionar_todo_pc(self):
        """Selecciona todo en la tabla de PCB."""
        if self.var_pc_select_all.get():
            self.tree_pc.selection_set(self.tree_pc.get_children())
        else:
            self.tree_pc.selection_remove(self.tree_pc.get_children())

    def buscar_registros_pc(self):
        """Consulta registros de trazabilidad PCB."""
        criterio = self.combo_pc_criterio.get()
        valor = f"%{self.var_pc_busqueda.get().strip()}%"

        mapa_columnas = {
            "Serial": "serial",
            "Work Order": "work_order",
            "P/N": "pn",
            "Lote": "lote",
            "Cantidad": "cantidad",
            "Fecha": "fecha"
        }

        for row in self.tree_pc.get_children():
            self.tree_pc.delete(row)

        self.var_pc_select_all.set(False)

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if criterio == "Todos" or not self.var_pc_busqueda.get().strip():
                        cur.execute("SELECT id, serial, work_order, pn, lote, cantidad, fecha FROM etiqueta_trazabilidad_qr_pcb ORDER BY id DESC")
                    else:
                        col = mapa_columnas[criterio]
                        query = sql.SQL("SELECT id, serial, work_order, pn, lote, cantidad, fecha FROM etiqueta_trazabilidad_qr_pcb WHERE {} ILIKE %s ORDER BY id DESC").format(sql.Identifier(col))
                        cur.execute(query, (valor,))
                    
                    rows = cur.fetchall()
                    for r in rows:
                        self.tree_pc.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error de Búsqueda", str(e))
            finally:
                conn.close()

    def mostrar_popup_etiqueta_pc(self):
        """Ventana modal preview para serial individual de PCB."""
        selected = self.tree_pc.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un registro primero.")
            return

        item_values = self.tree_pc.item(selected[0])['values']
        
        datos = {
            'serial': item_values[1],
            'work_order': item_values[2],
            'pn': item_values[3],
            'lote': item_values[4],
            'cantidad': item_values[5],
            'fecha': item_values[6]
        }

        popup = tk.Toplevel(self.root)
        popup.title(f"Vista Previa - {datos['serial']}")
        popup.geometry("450x250")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        # Carga del ícono (.ico)
        dir_raiz = Path(__file__).resolve().parent.parent
        ruta_icono = dir_raiz / "SistemaTrazabilidad.ico"

        if ruta_icono.exists():
            try:
                # Se le aplica directamente a la ventana emergente 'popup'
                popup.iconbitmap(ruta_icono)
            except Exception as e:
                print(f"Error al cargar el icono .ico en popup: {e}")

        img_pil = self.render_etiqueta_pc(datos)
        img_tk = ImageTk.PhotoImage(img_pil)

        lbl_img = ttk.Label(popup, image=img_tk, background="#f4f6f8")
        lbl_img.image = img_tk
        lbl_img.pack(expand=True, pady=15)

        ttk.Button(popup, text="Cerrar", style="Secondary.TButton", command=popup.destroy).pack(pady=(0, 15))

    def exportar_png_multiples_pc(self):
        """Exporta múltiples elementos PCB como archivos individuales PNG en una carpeta."""
        selected = self.tree_pc.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione al menos un registro para exportar.")
            return

        folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar imágenes PNG")
        if folder:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        for item in selected:
                            item_id = self.tree_pc.item(item)['values'][0]
                            cur.execute("SELECT serial, work_order, pn, lote, cantidad, fecha FROM etiqueta_trazabilidad_qr_pcb WHERE id = %s", (item_id,))
                            r = cur.fetchone()
                            if r:
                                datos = {'serial': r[0], 'work_order': r[1], 'pn': r[2], 'lote': r[3], 'cantidad': r[4], 'fecha': r[5]}
                                img = self.render_etiqueta_pc(datos)
                                img.save(os.path.join(folder, f"Etiqueta_PCB_{datos['serial']}.png"))
                    messagebox.showinfo("Éxito", f"Se exportaron {len(selected)} imágenes correctamente.")
                finally:
                    conn.close()

    def exportar_pdf_multiples_pc(self):
        """Exporta múltiples seriales PCB organizados óptimamente en PDF de páginas en rejilla o individuales."""
        selected = self.tree_pc.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione al menos un registro para exportar.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"Etiquetas_PCB_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        if not filepath:
            return

        from reportlab.lib.pagesizes import mm
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(filepath, pagesize=(40 * mm, 15 * mm))
        temp_files = []

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    for idx, item in enumerate(selected):
                        item_id = self.tree_pc.item(item)['values'][0]
                        cur.execute("SELECT serial, work_order, pn, lote, cantidad, fecha FROM etiqueta_trazabilidad_qr_pcb WHERE id = %s", (item_id,))
                        r = cur.fetchone()
                        if r:
                            datos = {'serial': r[0], 'work_order': r[1], 'pn': r[2], 'lote': r[3], 'cantidad': r[4], 'fecha': r[5]}
                            img = self.render_etiqueta_pc(datos)
                            temp_img_path = f"temp_pcb_{idx}.png"
                            img.save(temp_img_path)
                            temp_files.append(temp_img_path)
                            c.drawImage(temp_img_path, 0, 0, width=40*mm, height=15*mm)
                            c.showPage()
                c.save()
            finally:
                conn.close()

        for tmp in temp_files:
            if os.path.exists(tmp):
                os.remove(tmp)

        messagebox.showinfo("Exportado", f"Etiquetas PCB PDF guardadas en:\n{filepath}")

    def eliminar_registro_pc(self):
        """Elimina físicamente los registros PCB seleccionados de la base de datos."""
        selected = self.tree_pc.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione al menos un registro para eliminar.")
            return

        cant = len(selected)
        confirm = messagebox.askyesno("Eliminar Registros", f"¿Está seguro de eliminar {cant} registro(s) de PCB seleccionados?")
        if confirm:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        for item in selected:
                            item_id = self.tree_pc.item(item)['values'][0]
                            cur.execute("DELETE FROM etiqueta_trazabilidad_qr_pcb WHERE id = %s", (item_id,))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Se eliminaron {cant} registro(s) correctamente.")
                    self.buscar_registros_pc()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudieron eliminar los registros:\n{e}")
                finally:
                    conn.close()