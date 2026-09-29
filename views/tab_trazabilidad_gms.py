"""
===============================================================================
MÓDULO PESTAÑAS: TRAZABILIDAD QR M-G-S
===============================================================================
Maneja el registro, control, trazabilidad e impresión de muestras patrón:
Master, Golden y Silver.
===============================================================================
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from psycopg2 import sql

from config.database import get_db_connection
from utils.qr_generator import QRGenerator

class TabTrazabilidadGMS:
    def __init__(self, main_app, tab_generar, tab_consultar):
        self.main_app = main_app
        self.root = main_app.root
        self.tab_gms_generar = tab_generar
        self.tab_gms_consultar = tab_consultar

        # ---------------------------------------------------------------------
        # VARIABLES DE CONTROL DE TKINTER (Módulo: Trazabilidad QR M-G-S)
        # ---------------------------------------------------------------------
        self.var_gms_tipo = tk.StringVar(value="MASTER")
        self.var_gms_id_medusa = tk.StringVar(value="")
        self.var_gms_pn = tk.StringVar(value="")
        self.var_gms_serial = tk.StringVar(value="")
        self.var_gms_fecha = tk.StringVar(value=datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_gms_select_all = tk.BooleanVar(value=False)

        self.img_gms_etiqueta_pil = None

        # Inicialización de vistas
        self.setup_tab_gms_generar()
        self.setup_tab_gms_consultar()

    # =========================================================================
    # --- MÓDULO 5: TRAZABILIDAD QR M-G-S (MASTER, GOLDEN, SILVER) ---
    # =========================================================================
    def setup_tab_gms_generar(self):
        """Construye la interfaz de captura para muestras Máster, Golden y Silver."""
        panel_izq = ttk.Frame(self.tab_gms_generar, padding=15)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(panel_izq, text="Datos Muestras (Master / Golden / Silver)", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        fields = [
            ("ID Medusa *", self.var_gms_id_medusa),
            ("P/N *", self.var_gms_pn),
            ("Serial M-G-S *", self.var_gms_serial),
            ("Fecha *", self.var_gms_fecha),
        ]

        ttk.Label(panel_izq, text="Tipo de Muestra *").grid(row=1, column=0, sticky="w", pady=5)
        cb_tipo = ttk.Combobox(panel_izq, textvariable=self.var_gms_tipo, width=26, state="readonly")
        cb_tipo['values'] = ("MASTER", "GOLDEN", "SILVER")
        cb_tipo.grid(row=1, column=1, sticky="w", pady=5, padx=(5, 0))

        row = 2
        for label_text, var in fields:
            ttk.Label(panel_izq, text=label_text).grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(panel_izq, textvariable=var, width=28).grid(row=row, column=1, sticky="w", pady=5, padx=(5, 0))
            row += 1

        frame_botones = ttk.Frame(panel_izq)
        frame_botones.grid(row=row, column=0, columnspan=2, pady=20, sticky="ew")

        btn_generar = ttk.Button(frame_botones, text="GENERAR ETIQUETA", style="Primary.TButton", command=self.accion_generar_etiqueta_gms)
        btn_generar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_limpiar = ttk.Button(frame_botones, text="LIMPIAR CAMPOS", style="Secondary.TButton", command=self.limpiar_campos_gms)
        btn_limpiar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        panel_der = ttk.Frame(self.tab_gms_generar, padding=15)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.card_gms_preview = tk.Frame(panel_der, bg="#f0f0f0", bd=1, relief="solid", highlightthickness=1, highlightbackground="#dcdfe6")
        self.card_gms_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        lbl_titulo_preview = tk.Label(self.card_gms_preview, text="Vista previa 60 × 40 mm (M-G-S)", font=("Segoe UI", 9), bg="#f0f0f0", fg="#333333")
        lbl_titulo_preview.pack(anchor="nw", padx=8, pady=8)

        self.lbl_gms_preview = tk.Label(self.card_gms_preview, text="Captura los datos y pulsa GENERAR ETIQUETA", font=("Segoe UI", 10), bg="#f0f0f0", fg="#000000")
        self.lbl_gms_preview.pack(anchor="center", expand=True)

    def render_etiqueta_gms(self, datos):
        """Renderiza visualmente la etiqueta para muestras M-G-S."""
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='white')
        d = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arialbd.ttf", 22)
            medium_bold = ImageFont.truetype("arialbd.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = medium_bold = small_font = ImageFont.load_default()

        margin = 15

        d.text((margin + 100, margin), "Medusa Electronic S.A de C.V", fill='black', font=title_font)
        
        tipo_str = f"MUESTRA {datos['tipo']}"
        d.text((margin, margin + 44), tipo_str, fill='black', font=medium_bold)

        y = margin + 85
        spacing = 30

        items = [
            ("ID MEDUSA", datos['id_medusa']),
            ("P/N", datos['pn']),
            ("SERIAL", datos['serial']),
            ("FECHA", datos['fecha'])
        ]

        for label, val in items:
            d.text((margin, y), f"{label}: {val}"[:28], fill='black', font=small_font)
            y += spacing

        qr_content = f"TIPO: {datos['tipo']}\nID-MEDUSA: {datos['id_medusa']}\nPN: {datos['pn']}\nSERIAL: {datos['serial']}\nFECHA: {datos['fecha']}"
        
        qr_size = int(height * 0.45)
        qr_img = QRGenerator.make(qr_content, box_size=8)
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
        
        img.paste(qr_img, (width - qr_size - margin - 10, height - qr_size - margin - 30))

        d.rectangle((0, 0, width - 1, height - 1), outline="black", width=3)
        return img

    def accion_generar_etiqueta_gms(self):
        """Valida e inserta una nueva etiqueta Master/Golden/Silver en DB."""
        datos = {
            'tipo': self.var_gms_tipo.get().strip(),
            'id_medusa': self.var_gms_id_medusa.get().strip(),
            'pn': self.var_gms_pn.get().strip(),
            'serial': self.var_gms_serial.get().strip(),
            'fecha': self.var_gms_fecha.get().strip()
        }

        if not all(datos.values()):
            messagebox.showwarning("Campos Incompletos", "Todos los campos (Tipo, ID Medusa, P/N, Serial y Fecha) son obligatorios.")
            return

        self.img_gms_etiqueta_pil = self.render_etiqueta_gms(datos)
        img_tk = ImageTk.PhotoImage(self.img_gms_etiqueta_pil.resize((500, 333)))
        self.lbl_gms_preview.config(image=img_tk)
        self.lbl_gms_preview.image = img_tk

        confirm = messagebox.askyesno("Confirmar Registro", "¿Desea registrar esta muestra en la base de datos?")
        if confirm:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO etiqueta_trazabilidad_qr_gms (tipo, id_medusa, pn, serial, fecha)
                            VALUES (%s, %s, %s, %s, %s)
                        """, tuple(datos.values()))
                        conn.commit()
                    messagebox.showinfo("Éxito", "Muestra registrada correctamente.")
                    self.buscar_registros_gms()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudo guardar el registro M-G-S:\n{e}")
                finally:
                    conn.close()

    def limpiar_campos_gms(self):
        """Limpia los campos del módulo M-G-S."""
        self.var_gms_tipo.set("MASTER")
        self.var_gms_id_medusa.set("")
        self.var_gms_pn.set("")
        self.var_gms_serial.set("")
        self.var_gms_fecha.set(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.lbl_gms_preview.config(image="", text="Captura los datos y pulsa GENERAR ETIQUETA")
        self.lbl_gms_preview.image = None

    def setup_tab_gms_consultar(self):
        """Construye la interfaz de consulta para M-G-S."""
        panel_top = ttk.Frame(self.tab_gms_consultar, padding=10)
        panel_top.pack(fill=tk.X)

        ttk.Label(panel_top, text="Buscar por:").pack(side=tk.LEFT, padx=5)
        
        self.combo_gms_criterio = ttk.Combobox(panel_top, state="readonly", values=[
            "Todos", "Tipo", "ID Medusa", "P/N", "Serial", "Fecha"
        ])
        self.combo_gms_criterio.current(0)
        self.combo_gms_criterio.pack(side=tk.LEFT, padx=5)

        self.var_gms_busqueda = tk.StringVar()
        ttk.Entry(panel_top, textvariable=self.var_gms_busqueda, width=25).pack(side=tk.LEFT, padx=5)

        btn_buscar = ttk.Button(panel_top, text="Buscar", style="Primary.TButton", command=self.buscar_registros_gms)
        btn_buscar.pack(side=tk.LEFT, padx=5)

        chk_all = ttk.Checkbutton(
            panel_top, 
            text="Seleccionar Todo", 
            variable=self.var_gms_select_all, 
            command=self.toggle_seleccionar_todo_gms
        )
        chk_all.pack(side=tk.RIGHT, padx=10)

        columns = ("db_id", "tipo", "id_medusa", "pn", "serial", "fecha")
        self.tree_gms = ttk.Treeview(self.tab_gms_consultar, columns=columns, show="headings", selectmode="extended", height=12)
        
        self.tree_gms.configure(displaycolumns=("tipo", "id_medusa", "pn", "serial", "fecha"))

        self.tree_gms.heading("tipo", text="Tipo Muestra")
        self.tree_gms.heading("id_medusa", text="ID Medusa")
        self.tree_gms.heading("pn", text="P/N")
        self.tree_gms.heading("serial", text="Serial")
        self.tree_gms.heading("fecha", text="Fecha")

        self.tree_gms.column("tipo", width=100)
        self.tree_gms.column("id_medusa", width=120)
        self.tree_gms.column("pn", width=120)
        self.tree_gms.column("serial", width=120)
        self.tree_gms.column("fecha", width=100)

        self.tree_gms.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree_gms.bind("<Double-1>", lambda event: self.mostrar_popup_etiqueta_gms())

        panel_acciones = ttk.Frame(self.tab_gms_consultar, padding=10)
        panel_acciones.pack(fill=tk.X)

        ttk.Button(panel_acciones, text="Ver Etiqueta", style="Primary.TButton", command=self.mostrar_popup_etiqueta_gms).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Exportar Seleccionados (PNG)", style="Secondary.TButton", command=self.exportar_png_multiples_gms).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Exportar Seleccionados (PDF)", style="Secondary.TButton", command=self.exportar_pdf_multiples_gms).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Eliminar Seleccionados", style="Danger.TButton", command=self.eliminar_registro_gms).pack(side=tk.RIGHT, padx=5)

        self.buscar_registros_gms()

    def toggle_seleccionar_todo_gms(self):
        """Selecciona o deselecciona todas las filas M-G-S."""
        if self.var_gms_select_all.get():
            self.tree_gms.selection_set(self.tree_gms.get_children())
        else:
            self.tree_gms.selection_remove(self.tree_gms.get_children())

    def buscar_registros_gms(self):
        """Realiza la búsqueda de muestras en DB."""
        criterio = self.combo_gms_criterio.get()
        valor = f"%{self.var_gms_busqueda.get().strip()}%"

        mapa_columnas = {
            "Tipo": "tipo",
            "ID Medusa": "id_medusa",
            "P/N": "pn",
            "Serial": "serial",
            "Fecha": "fecha"
        }

        for row in self.tree_gms.get_children():
            self.tree_gms.delete(row)

        self.var_gms_select_all.set(False)

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if criterio == "Todos" or not self.var_gms_busqueda.get().strip():
                        cur.execute("SELECT id, tipo, id_medusa, pn, serial, fecha FROM etiqueta_trazabilidad_qr_gms ORDER BY id DESC")
                    else:
                        col = mapa_columnas[criterio]
                        query = sql.SQL("SELECT id, tipo, id_medusa, pn, serial, fecha FROM etiqueta_trazabilidad_qr_gms WHERE {} ILIKE %s ORDER BY id DESC").format(sql.Identifier(col))
                        cur.execute(query, (valor,))
                    
                    rows = cur.fetchall()
                    for r in rows:
                        self.tree_gms.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error de Búsqueda", str(e))
            finally:
                conn.close()

    def mostrar_popup_etiqueta_gms(self):
        """Muestra ventana con la etiqueta en grande."""
        selected = self.tree_gms.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un registro primero.")
            return

        item_values = self.tree_gms.item(selected[0])['values']
        
        datos = {
            'tipo': item_values[1],
            'id_medusa': item_values[2],
            'pn': item_values[3],
            'serial': item_values[4],
            'fecha': item_values[5]
        }

        popup = tk.Toplevel(self.root)
        popup.title(f"Vista Previa M-G-S - {datos['serial']}")
        popup.geometry("800x600")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        img_pil = self.render_etiqueta_gms(datos)
        img_tk = ImageTk.PhotoImage(img_pil.resize((720, 480)))

        lbl_img = ttk.Label(popup, image=img_tk, background="#f4f6f8")
        lbl_img.image = img_tk
        lbl_img.pack(expand=True, pady=15)

        ttk.Button(popup, text="Cerrar", style="Secondary.TButton", command=popup.destroy).pack(pady=(0, 15))

    def exportar_png_multiples_gms(self):
        """Guarda en PNG los elementos M-G-S seleccionados."""
        selected = self.tree_gms.selection()
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
                            item_id = self.tree_gms.item(item)['values'][0]
                            cur.execute("SELECT tipo, id_medusa, pn, serial, fecha FROM etiqueta_trazabilidad_qr_gms WHERE id = %s", (item_id,))
                            r = cur.fetchone()
                            if r:
                                datos = {'tipo': r[0], 'id_medusa': r[1], 'pn': r[2], 'serial': r[3], 'fecha': r[4]}
                                img = self.render_etiqueta_gms(datos)
                                img.save(os.path.join(folder, f"Etiqueta_GMS_{datos['serial']}.png"))
                    messagebox.showinfo("Éxito", f"Se exportaron {len(selected)} imágenes correctamente.")
                finally:
                    conn.close()

    def exportar_pdf_multiples_gms(self):
        """Exporta muestras M-G-S a PDF."""
        selected = self.tree_gms.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione al menos un registro para exportar.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"Etiquetas_GMS_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        if not filepath:
            return

        from reportlab.lib.pagesizes import mm
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(filepath, pagesize=(60 * mm, 40 * mm))
        temp_files = []

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    for idx, item in enumerate(selected):
                        item_id = self.tree_gms.item(item)['values'][0]
                        cur.execute("SELECT tipo, id_medusa, pn, serial, fecha FROM etiqueta_trazabilidad_qr_gms WHERE id = %s", (item_id,))
                        r = cur.fetchone()
                        if r:
                            datos = {'tipo': r[0], 'id_medusa': r[1], 'pn': r[2], 'serial': r[3], 'fecha': r[4]}
                            img = self.render_etiqueta_gms(datos)
                            temp_img_path = f"temp_gms_{idx}.png"
                            img.save(temp_img_path)
                            temp_files.append(temp_img_path)
                            c.drawImage(temp_img_path, 0, 0, width=60*mm, height=40*mm)
                            c.showPage()
                c.save()
            finally:
                conn.close()

        for tmp in temp_files:
            if os.path.exists(tmp):
                os.remove(tmp)

        messagebox.showinfo("Exportado", f"Etiquetas GMS PDF guardadas en:\n{filepath}")

    def eliminar_registro_gms(self):
        """Elimina de la base de datos los registros M-G-S seleccionados."""
        selected = self.tree_gms.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione al menos un registro para eliminar.")
            return

        cant = len(selected)
        confirm = messagebox.askyesno("Eliminar Registros", f"¿Está seguro de eliminar {cant} registro(s) seleccionados?")
        if confirm:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        for item in selected:
                            item_id = self.tree_gms.item(item)['values'][0]
                            cur.execute("DELETE FROM etiqueta_trazabilidad_qr_gms WHERE id = %s", (item_id,))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Se eliminaron {cant} registro(s) correctamente.")
                    self.buscar_registros_gms()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudieron eliminar los registros:\n{e}")
                finally:
                    conn.close()