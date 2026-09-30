"""
===============================================================================
MÓDULO PESTAÑAS: PRODUCTO TERMINADO (PT)
===============================================================================
Maneja la generación y trazabilidad de etiquetas de entregas, notas de envío y
producto final preparado para cliente/embarque.
===============================================================================
"""

import os
from pathlib import Path
import datetime
import tkinter as tk
import textwrap
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from psycopg2 import sql

from config.database import get_db_connection
from utils.qr_generator import QRGenerator
from utils.validators import es_numero_valido

class TabProductoTerminado:
    def __init__(self, main_app, tab_generar, tab_consultar):
        self.main_app = main_app
        self.root = main_app.root
        self.tab_pt_generar = tab_generar
        self.tab_pt_consultar = tab_consultar

        # ---------------------------------------------------------------------
        # VARIABLES DE CONTROL DE TKINTER (Módulo: Producto Terminado)
        # ---------------------------------------------------------------------
        self.var_pt_id_entrega = tk.StringVar()
        self.var_pt_delivery_note = tk.StringVar(value="")
        self.var_pt_cliente = tk.StringVar(value="")
        self.var_pt_orden_venta = tk.StringVar(value="")
        self.var_pt_codigo_prod = tk.StringVar(value="")
        self.var_pt_descripcion = tk.StringVar(value="")
        self.var_pt_lote = tk.StringVar(value="")
        self.var_pt_cantidad = tk.StringVar(value="")
        self.var_pt_unidad = tk.StringVar(value="pz")
        self.var_pt_f_entrega = tk.StringVar(value=datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_pt_no_guia = tk.StringVar(value="")
        self.var_pt_destino = tk.StringVar(value="")
        self.var_pt_estado = tk.StringVar(value="")
        self.var_pt_select_all = tk.BooleanVar(value=False)

        # Variables de control para desglose de dirección de envío (emergente)
        self.var_dir_calle = tk.StringVar(value="")
        self.var_dir_colonia = tk.StringVar(value="")
        self.var_dir_ciudad = tk.StringVar(value="")
        self.var_dir_estado_prov = tk.StringVar(value="")
        self.var_dir_cp = tk.StringVar(value="")
        self.var_dir_pais = tk.StringVar(value="")

        self.img_pt_etiqueta_pil = None
        self.generar_nuevo_id_pt()

        # Inicializar UI
        self.setup_tab_pt_generar()
        self.setup_tab_pt_consultar()

    def generar_nuevo_id_pt(self):
        """Genera un folio único con la sintaxis PT-AAAAMMDD-HHMMSS para Producto Terminado."""
        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.var_pt_id_entrega.set(f"PT-{now_str}")

    def limpiar_campos_pt(self):
        """Limpia los campos del formulario de Producto Terminado."""
        self.generar_nuevo_id_pt()
        self.var_pt_delivery_note.set("")
        self.var_pt_cliente.set("")
        self.var_pt_orden_venta.set("")
        self.var_pt_codigo_prod.set("")
        self.var_pt_descripcion.set("")
        self.var_pt_lote.set("")
        self.var_pt_cantidad.set("")
        self.var_pt_unidad.set("pz")
        self.var_pt_f_entrega.set(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_pt_no_guia.set("")
        self.var_pt_destino.set("")
        self.var_pt_estado.set("")

        # Limpiar variables secundarias del formulario emergente de dirección
        self.var_dir_calle.set("")
        self.var_dir_colonia.set("")
        self.var_dir_ciudad.set("")
        self.var_dir_estado_prov.set("")
        self.var_dir_cp.set("")
        self.var_dir_pais.set("")

        self.img_pt_etiqueta_pil = None
        self.lbl_pt_preview.config(image="", text="Captura los datos y pulsa GENERAR ETIQUETA")
        self.lbl_pt_preview.image = None

    def abrir_modal_direccion(self):
        """Abre ventana emergente para capturar formulario de dirección de envío y No. de guía."""
        popup = tk.Toplevel(self.root)
        popup.title("Dirección de Envío y Guía")
        popup.geometry("450x380")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        ttk.Label(popup, text="Dirección de Envío y No. de Guía", style="Header.TLabel").pack(pady=10)

        frame_form = ttk.Frame(popup, padding=10)
        frame_form.pack(fill=tk.BOTH, expand=True)

        campos_dir = [
            ("Calle y No.:", self.var_dir_calle),
            ("Colonia:", self.var_dir_colonia),
            ("Ciudad / Municipio:", self.var_dir_ciudad),
            ("Estado / Prov.:", self.var_dir_estado_prov),
            ("Código Postal:", self.var_dir_cp),
            ("País:", self.var_dir_pais),
            ("No. de Guía:", self.var_pt_no_guia)
        ]

        for i, (lbl_txt, var) in enumerate(campos_dir):
            ttk.Label(frame_form, text=lbl_txt).grid(row=i, column=0, sticky="w", pady=3, padx=5)
            ttk.Entry(frame_form, textvariable=var, width=30).grid(row=i, column=1, sticky="w", pady=3, padx=5)

        def guardar_direccion():
            # Concatenar componentes para formar el String completo de Destino
            partes = [
                self.var_dir_calle.get().strip(),
                self.var_dir_colonia.get().strip(),
                self.var_dir_ciudad.get().strip(),
                self.var_dir_estado_prov.get().strip(),
                self.var_dir_cp.get().strip(),
                self.var_dir_pais.get().strip()
            ]
            destino_full = ", ".join([p for p in partes if p])
            self.var_pt_destino.set(destino_full)
            popup.destroy()

        frame_btns = ttk.Frame(popup, padding=10)
        frame_btns.pack(fill=tk.X)

        ttk.Button(frame_btns, text="Guardar Dirección", style="Primary.TButton", command=guardar_direccion).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(frame_btns, text="Cancelar", style="Secondary.TButton", command=popup.destroy).pack(side=tk.RIGHT, padx=5, expand=True)

    # =========================================================================
    # --- MÓDULO 3: PRODUCTO TERMINADO (PT) ---
    # =========================================================================
    def setup_tab_pt_generar(self):
        """Construye la UI para la captura y generación de etiquetas de Producto Terminado."""
        panel_izq = ttk.Frame(self.tab_pt_generar, padding=15)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(panel_izq, text="Datos de Producto Terminado", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        vcmd = (self.root.register(es_numero_valido), '%P')

        fields_req = [
            ("ID Producto Terminado *", self.var_pt_id_entrega, True, False),
            ("Delivery Note ERPNext *", self.var_pt_delivery_note, False, False),
            ("Cliente *", self.var_pt_cliente, False, False),
            ("Orden de venta *", self.var_pt_orden_venta, False, False),
            ("Código de producto *", self.var_pt_codigo_prod, False, False),
            ("Descripción *", self.var_pt_descripcion, False, False),
            ("Lote *", self.var_pt_lote, False, False),
        ]

        row = 1
        for label_text, var, readonly, es_num in fields_req:
            ttk.Label(panel_izq, text=label_text).grid(row=row, column=0, sticky="w", pady=3)
            state = "readonly" if readonly else "normal"
            ttk.Entry(panel_izq, textvariable=var, state=state, width=28).grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
            row += 1

        ttk.Label(panel_izq, text="Cantidad *").grid(row=row, column=0, sticky="w", pady=3)
        frame_cant = ttk.Frame(panel_izq)
        frame_cant.grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        
        ttk.Entry(frame_cant, textvariable=self.var_pt_cantidad, width=15, validate="key", validatecommand=vcmd).pack(side=tk.LEFT, padx=(0, 5))
        cb_unidad = ttk.Combobox(frame_cant, textvariable=self.var_pt_unidad, width=8, state="readonly")
        cb_unidad['values'] = ("pz", "kg", "lts", "oz", "mtr", "gal", "ft", "paq")
        cb_unidad.pack(side=tk.LEFT)
        row += 1

        ttk.Label(panel_izq, text="Fecha de entrega *").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(panel_izq, textvariable=self.var_pt_f_entrega, width=28).grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        row += 1

        # Botón para la apertura del formulario modal de Dirección de Envío y Guía
        btn_agregar_dir = ttk.Button(panel_izq, text="Agregar Dirección", style="Secondary.TButton", command=self.abrir_modal_direccion)
        btn_agregar_dir.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(5, 5))
        row += 1

        ttk.Label(panel_izq, text="Opcionales", font=("Segoe UI", 9, "bold", "italic")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 2))
        row += 1

        ttk.Label(panel_izq, text="Estado *").grid(row=row, column=0, sticky="w", pady=3)
        cb_estado_pt = ttk.Combobox(panel_izq, textvariable=self.var_pt_estado, width=26, state="readonly")
        cb_estado_pt['values'] = ("", "EMPACADO", "LISTO PARA ENVÍO", "ENVIADO")
        cb_estado_pt.grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        row += 1

        frame_botones = ttk.Frame(panel_izq)
        frame_botones.grid(row=row, column=0, columnspan=2, pady=15, sticky="ew")

        btn_generar = ttk.Button(frame_botones, text="GENERAR ETIQUETA", style="Primary.TButton", command=self.accion_generar_etiqueta_pt)
        btn_generar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_limpiar = ttk.Button(frame_botones, text="LIMPIAR CAMPOS", style="Secondary.TButton", command=self.limpiar_campos_pt)
        btn_limpiar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        panel_der = ttk.Frame(self.tab_pt_generar, padding=15)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.card_pt_preview = tk.Frame(panel_der, bg="#f0f0f0", bd=1, relief="solid", highlightthickness=1, highlightbackground="#dcdfe6")
        self.card_pt_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        lbl_titulo_preview = tk.Label(self.card_pt_preview, text="Vista previa 60 × 40 mm", font=("Segoe UI", 9), bg="#f0f0f0", fg="#333333")
        lbl_titulo_preview.pack(anchor="nw", padx=8, pady=8)

        self.lbl_pt_preview = tk.Label(self.card_pt_preview, text="Captura los datos y pulsa GENERAR ETIQUETA", font=("Segoe UI", 10), bg="#f0f0f0", fg="#000000")
        self.lbl_pt_preview.pack(anchor="center", expand=True)

    def render_etiqueta_pt(self, datos):
        """Genera el mapa de bits con Pillow para la etiqueta de Producto Terminado."""
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='white')
        d = ImageDraw.Draw(img)

        try:
            medium_bold = ImageFont.truetype("arialbd.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 15)
        except:
            medium_bold = small_font = ImageFont.load_default()

        margin = 15

        # Búsqueda y renderizado del logotipo en la esquina superior derecha
        dir_base = Path(__file__).resolve().parent.parent
        posibles_rutas = [
            dir_base / "Medusa_Logo_Sin_Fondo.png",
            dir_base / "assets" / "logo.png",
            dir_base / "logo.png"
        ]

        logo_path = None
        for ruta in posibles_rutas:
            if ruta.exists():
                logo_path = ruta
                break

        if logo_path:
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_width = 180
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            logo_resized = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            logo_x = width - margin - logo_width - 10
            logo_y = margin
            img.paste(logo_resized, (logo_x, logo_y), logo_resized)
        
        # Código de producto en la parte superior
        prod_texto = f"COD-PROD : {datos['codigo_producto']}"
        d.text((margin, margin), prod_texto[:28], fill='black', font=medium_bold)

        y = margin + 35
        line_spacing = 20  # Altura por línea de texto
        
        items = [
            ("ID-PT", datos['id_entrega']),
            ("DN-ERP", datos['delivery_note_erp']),
            ("CLI", datos['cliente']),
            ("OV", datos['orden_venta']),
            ("CANT", datos['cantidad']),
            ("LOTE", datos['lote']),
            ("FECHA-ENTREGA", datos['fecha_entrega']),
        ]

        if datos['no_guia']:
            items.append(("GUIA", datos['no_guia']))
        if datos['destino']:
            items.append(("DEST", datos['destino']))
        if datos['estado']:
            items.append(("EST", datos['estado']))

        # Ancho máximo en caracteres por línea para no invadir el QR o logotipo
        max_char_width = 28

        for label, val in items:
            texto_completo = f"{label}: {val}"
            
            # Para Cliente y Destino se aplica multilinea automática si sobrepasan los caracteres permitidos
            if label in ("CLI", "DEST") and len(texto_completo) > max_char_width:
                lineas = textwrap.wrap(texto_completo, width=max_char_width)
                for linea in lineas:
                    d.text((margin, y), linea, fill='black', font=small_font)
                    y += line_spacing
            else:
                d.text((margin, y), texto_completo[:max_char_width], fill='black', font=small_font)
                y += line_spacing

        qr_content = (
            f"ID-PT: {datos['id_entrega']}\n"
            f"DN-ERP: {datos['delivery_note_erp']}\n"
            f"CLI: {datos['cliente']}\n"
            f"OV: {datos['orden_venta']}\n"
            f"COD-PROD: {datos['codigo_producto']}\n"
            f"CANT: {datos['cantidad']}\n"
            f"LOT: {datos['lote']}\n"
            f"FECHA-ENTREGA: {datos['fecha_entrega']}\n"
            f"GUIA: {datos['no_guia']}\n"
            f"DEST: {datos['destino']}\n"
            f"EST: {datos['estado']}"
        )
        
        qr_size = int(height * 0.42)
        qr_img = QRGenerator.make(qr_content, box_size=8)
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
        
        img.paste(qr_img, (width - qr_size - margin - 5, height - qr_size - margin - 20))

        if datos['descripcion']:
            # Ajusta la descripción en líneas al pie de la etiqueta
            desc_multiline = textwrap.fill(datos['descripcion'], width=35)
            lineas = desc_multiline.count('\n') + 1
            y_desc = height - (18 * lineas) - 10
            d.text((margin, y_desc), desc_multiline, fill='black', font=small_font)

        d.rectangle((0, 0, width - 1, height - 1), outline="black", width=3)
        return img

    def accion_generar_etiqueta_pt(self):
        """Valida y registra la etiqueta de Producto Terminado en DB."""
        cant_num = self.var_pt_cantidad.get().strip()
        unidad = self.var_pt_unidad.get().strip()
        cantidad_completa = f"{cant_num} {unidad}".strip()

        datos = {
            'id_entrega': self.var_pt_id_entrega.get().strip(),
            'delivery_note_erp': self.var_pt_delivery_note.get().strip(),
            'cliente': self.var_pt_cliente.get().strip(),
            'orden_venta': self.var_pt_orden_venta.get().strip(),
            'codigo_producto': self.var_pt_codigo_prod.get().strip(),
            'descripcion': self.var_pt_descripcion.get().strip(),
            'lote': self.var_pt_lote.get().strip(),
            'cantidad': cantidad_completa,
            'fecha_entrega': self.var_pt_f_entrega.get().strip(),
            'no_guia': self.var_pt_no_guia.get().strip(),
            'destino': self.var_pt_destino.get().strip(),
            'estado': self.var_pt_estado.get().strip()
        }

        if not cant_num:
            messagebox.showwarning("Campos Incompletos", "Por favor ingrese un valor numérico para la cantidad.")
            return

        campos_obligatorios = {
            'id_entrega': datos['id_entrega'],
            'delivery_note_erp': datos['delivery_note_erp'],
            'cliente': datos['cliente'],
            'orden_venta': datos['orden_venta'],
            'codigo_producto': datos['codigo_producto'],
            'descripcion': datos['descripcion'],
            'lote': datos['lote'],
            'fecha_entrega': datos['fecha_entrega'],
            'estado': datos['estado']
        }

        for campo, valor in campos_obligatorios.items():
            if not valor:
                messagebox.showwarning("Campos Incompletos", f"El campo {campo.replace('_', ' ').title()} es obligatorio.")
                return

        self.img_pt_etiqueta_pil = self.render_etiqueta_pt(datos)
        img_tk = ImageTk.PhotoImage(self.img_pt_etiqueta_pil.resize((500, 333)))
        self.lbl_pt_preview.config(image=img_tk)
        self.lbl_pt_preview.image = img_tk

        respuesta = messagebox.askyesno("Confirmar Registro", "¿Desea registrar esta etiqueta de Producto Terminado en la base de datos?")

        if respuesta:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO etiquetas_producto_terminado (
                                id_entrega, delivery_note_erp, cliente, orden_venta, codigo_producto,
                                descripcion, lote, cantidad, fecha_entrega, no_guia, destino, estado
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, tuple(datos.values()))
                        conn.commit()
                    messagebox.showinfo("Éxito", "Etiqueta de Producto Terminado registrada correctamente.")
                    self.buscar_registros_pt()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudo guardar la etiqueta PT:\n{e}")
                finally:
                    conn.close()

    def setup_tab_pt_consultar(self):
        """Construye la UI de consulta y exportación de Producto Terminado."""
        panel_top = ttk.Frame(self.tab_pt_consultar, padding=10)
        panel_top.pack(fill=tk.X)

        ttk.Label(panel_top, text="Buscar por:").pack(side=tk.LEFT, padx=5)
        
        self.combo_pt_criterio = ttk.Combobox(panel_top, state="readonly", values=[
            "Todos", "ID entrega", "Delivery Note ERP", "Cliente", "Orden de venta", "Código producto", 
            "Descripción", "Lote", "Cantidad", "Fecha entrega", "No. guía", "Destino", "Estado"
        ])
        self.combo_pt_criterio.current(0)
        self.combo_pt_criterio.pack(side=tk.LEFT, padx=5)

        self.var_pt_busqueda = tk.StringVar()
        ttk.Entry(panel_top, textvariable=self.var_pt_busqueda, width=25).pack(side=tk.LEFT, padx=5)

        btn_buscar = ttk.Button(panel_top, text="Buscar", style="Primary.TButton", command=self.buscar_registros_pt)
        btn_buscar.pack(side=tk.LEFT, padx=5)

        chk_all = ttk.Checkbutton(
            panel_top, 
            text="Seleccionar Todo", 
            variable=self.var_pt_select_all, 
            command=self.toggle_seleccionar_todo_pt
        )
        chk_all.pack(side=tk.RIGHT, padx=10)

        columns = ("db_id", "id_entrega", "delivery_note_erp", "cliente", "orden_venta", "codigo_producto", "lote", "cantidad", "estado")
        self.tree_pt = ttk.Treeview(self.tab_pt_consultar, columns=columns, show="headings", selectmode="extended", height=12)
        
        self.tree_pt.configure(displaycolumns=("id_entrega", "delivery_note_erp", "cliente", "orden_venta", "codigo_producto", "lote", "cantidad", "estado"))

        self.tree_pt.heading("id_entrega", text="ID Entrega")
        self.tree_pt.heading("delivery_note_erp", text="Delivery Note ERP")
        self.tree_pt.heading("cliente", text="Cliente")
        self.tree_pt.heading("orden_venta", text="Orden de Venta")
        self.tree_pt.heading("codigo_producto", text="Código Producto")
        self.tree_pt.heading("lote", text="Lote")
        self.tree_pt.heading("cantidad", text="Cantidad")
        self.tree_pt.heading("estado", text="Estado")

        self.tree_pt.column("id_entrega", width=120)
        self.tree_pt.column("delivery_note_erp", width=120)
        self.tree_pt.column("cliente", width=120)
        self.tree_pt.column("orden_venta", width=110)
        self.tree_pt.column("codigo_producto", width=110)
        self.tree_pt.column("lote", width=90)
        self.tree_pt.column("cantidad", width=80)
        self.tree_pt.column("estado", width=90)

        self.tree_pt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree_pt.bind("<Double-1>", lambda event: self.mostrar_popup_etiqueta_pt())

        panel_acciones = ttk.Frame(self.tab_pt_consultar, padding=10)
        panel_acciones.pack(fill=tk.X)

        ttk.Button(panel_acciones, text="Ver Etiqueta", style="Primary.TButton", command=self.mostrar_popup_etiqueta_pt).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Cambiar Estado", style="Primary.TButton", command=self.popup_cambiar_estado_pt).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Descargar (PNG)", style="Secondary.TButton", command=self.exportar_png_pt).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Descargar (PDF)", style="Secondary.TButton", command=self.exportar_pdf_pt).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Eliminar Seleccionados", style="Danger.TButton", command=self.eliminar_registro_pt).pack(side=tk.RIGHT, padx=5)

        self.buscar_registros_pt()

    def toggle_seleccionar_todo_pt(self):
        """Selecciona o deselecciona todas las filas en el Treeview de PT."""
        if self.var_pt_select_all.get():
            self.tree_pt.selection_set(self.tree_pt.get_children())
        else:
            self.tree_pt.selection_remove(self.tree_pt.get_children())

    def buscar_registros_pt(self):
        """Filtra y lista los registros de Producto Terminado desde la base de datos."""
        criterio = self.combo_pt_criterio.get()
        valor = f"%{self.var_pt_busqueda.get().strip()}%"

        mapa_columnas = {
            "ID entrega": "id_entrega",
            "Delivery Note ERP": "delivery_note_erp",
            "Cliente": "cliente",
            "Orden de venta": "orden_venta",
            "Código producto": "codigo_producto",
            "Descripción": "descripcion",
            "Lote": "lote",
            "Cantidad": "cantidad",
            "Fecha entrega": "fecha_entrega",
            "No. guía": "no_guia",
            "Destino": "destino",
            "Estado": "estado"
        }

        for row in self.tree_pt.get_children():
            self.tree_pt.delete(row)

        self.var_pt_select_all.set(False)

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if criterio == "Todos" or not self.var_pt_busqueda.get().strip():
                        cur.execute("SELECT id, id_entrega, delivery_note_erp, cliente, orden_venta, codigo_producto, lote, cantidad, estado FROM etiquetas_producto_terminado ORDER BY id DESC")
                    else:
                        col = mapa_columnas[criterio]
                        query = sql.SQL("SELECT id, id_entrega, delivery_note_erp, cliente, orden_venta, codigo_producto, lote, cantidad, estado FROM etiquetas_producto_terminado WHERE {} ILIKE %s ORDER BY id DESC").format(sql.Identifier(col))
                        cur.execute(query, (valor,))
                    
                    rows = cur.fetchall()
                    for r in rows:
                        self.tree_pt.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error de Búsqueda", str(e))
            finally:
                conn.close()

    def _obtener_datos_pt_seleccionados(self):
        """Obtiene el objeto de datos de la fila PT actualmente seleccionada."""
        selected = self.tree_pt.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un registro de producto terminado primero.")
            return None, None

        item_id = self.tree_pt.item(selected[0])['values'][0]
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id_entrega, delivery_note_erp, cliente, orden_venta, codigo_producto,
                               descripcion, lote, cantidad, fecha_entrega, no_guia, destino, estado
                        FROM etiquetas_producto_terminado WHERE id = %s
                    """, (item_id,))
                    r = cur.fetchone()
                    datos = {
                        'id_entrega': r[0], 'delivery_note_erp': r[1] or "", 'cliente': r[2], 'orden_venta': r[3],
                        'codigo_producto': r[4], 'descripcion': r[5], 'lote': r[6], 'cantidad': r[7],
                        'fecha_entrega': r[8], 'no_guia': r[9] or "", 'destino': r[10] or "", 'estado': r[11] or ""
                    }
                    return item_id, datos
            finally:
                conn.close()
        return None, None

    def popup_cambiar_estado_pt(self):
        """Abre ventana emergente Toplevel para actualizar el estado de Producto Terminado."""
        item_id, datos = self._obtener_datos_pt_seleccionados()
        if not datos:
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Cambiar Estado PT - {datos['id_entrega']}")
        popup.geometry("400x230")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        ttk.Label(popup, text=f"Cambiar Estado de {datos['id_entrega']}", style="Header.TLabel").pack(pady=15)

        frame_fields = ttk.Frame(popup, padding=10)
        frame_fields.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame_fields, text="Estado actual:").grid(row=0, column=0, sticky="w", pady=6, padx=5)
        estado_actual_txt = datos['estado'] if datos['estado'] else "(Sin asignar)"
        ttk.Label(frame_fields, text=estado_actual_txt, font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", pady=6, padx=5)

        ttk.Label(frame_fields, text="Nuevo estado:").grid(row=1, column=0, sticky="w", pady=6, padx=5)
        
        var_nuevo_estado = tk.StringVar(value=datos['estado'])
        cb_nuevo_estado = ttk.Combobox(frame_fields, textvariable=var_nuevo_estado, width=22, state="readonly")
        cb_nuevo_estado['values'] = ("EMPACADO", "LISTO PARA ENVÍO", "ENVIADO", "CUARENTENA", "RECHAZADO")
        cb_nuevo_estado.grid(row=1, column=1, sticky="w", pady=6, padx=5)

        def procesar_cambio_estado():
            nuevo_estado = var_nuevo_estado.get().strip()
            if not nuevo_estado:
                messagebox.showwarning("Atención", "Seleccione el nuevo estado.", parent=popup)
                return

            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE etiquetas_producto_terminado SET estado = %s WHERE id = %s", (nuevo_estado, item_id))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Estado actualizado correctamente a '{nuevo_estado}'.", parent=popup)
                    popup.destroy()
                    self.buscar_registros_pt()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudo actualizar el estado:\n{e}", parent=popup)
                finally:
                    conn.close()

        frame_btns = ttk.Frame(popup, padding=10)
        frame_btns.pack(fill=tk.X)

        ttk.Button(frame_btns, text="Guardar Estado", style="Primary.TButton", command=procesar_cambio_estado).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(frame_btns, text="Cancelar", style="Secondary.TButton", command=popup.destroy).pack(side=tk.RIGHT, padx=5, expand=True)

    def mostrar_popup_etiqueta_pt(self):
        """Abre ventana modal con la vista previa de la etiqueta PT."""
        item_id, datos = self._obtener_datos_pt_seleccionados()
        if not datos:
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Vista Previa - {datos['id_entrega']}")
        popup.geometry("800x600")
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

        img_pil = self.render_etiqueta_pt(datos)
        img_tk = ImageTk.PhotoImage(img_pil.resize((720, 480)))

        lbl_img = ttk.Label(popup, image=img_tk, background="#f4f6f8")
        lbl_img.image = img_tk
        lbl_img.pack(expand=True, pady=15)

        ttk.Button(popup, text="Cerrar", style="Secondary.TButton", command=popup.destroy).pack(pady=(0, 15))

    def exportar_png_pt(self):
        """Exporta en formato PNG uno o múltiples elementos PT seleccionados."""
        selected_items = self.tree_pt.selection()
        if not selected_items:
            messagebox.showwarning("Atención", "Seleccione al menos una etiqueta.")
            return

        if len(selected_items) == 1:
            item_id, datos = self._obtener_datos_pt_seleccionados()
            if datos:
                filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")], initialfile=f"Etiqueta_PT_{datos['id_entrega']}.png")
                if filepath:
                    img = self.render_etiqueta_pt(datos)
                    img.save(filepath)
                    messagebox.showinfo("Exportado", f"Etiqueta PT guardada en:\n{filepath}")
        else:
            folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar imágenes PNG")
            if folder:
                conn = get_db_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            for item in selected_items:
                                item_id = self.tree_pt.item(item)['values'][0]
                                cur.execute("SELECT id_entrega, delivery_note_erp, cliente, orden_venta, codigo_producto, descripcion, lote, cantidad, fecha_entrega, no_guia, destino, estado FROM etiquetas_producto_terminado WHERE id = %s", (item_id,))
                                r = cur.fetchone()
                                if r:
                                    datos = {
                                        'id_entrega': r[0], 'delivery_note_erp': r[1] or "", 'cliente': r[2], 'orden_venta': r[3],
                                        'codigo_producto': r[4], 'descripcion': r[5], 'lote': r[6], 'cantidad': r[7],
                                        'fecha_entrega': r[8], 'no_guia': r[9] or "", 'destino': r[10] or "", 'estado': r[11] or ""
                                    }
                                    img = self.render_etiqueta_pt(datos)
                                    img.save(os.path.join(folder, f"Etiqueta_PT_{datos['id_entrega']}.png"))
                        messagebox.showinfo("Exportado", f"Se exportaron {len(selected_items)} imágenes PNG en:\n{folder}")
                    finally:
                        conn.close()

    def exportar_pdf_pt(self):
        """Exporta los elementos seleccionados de PT a un documento PDF de 60x40mm por página."""
        selected_items = self.tree_pt.selection()
        if not selected_items:
            messagebox.showwarning("Atención", "Seleccione al menos un registro de la lista.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"Etiquetas_PT_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
                    for idx, item in enumerate(selected_items):
                        item_id = self.tree_pt.item(item)['values'][0]
                        cur.execute("SELECT id_entrega, delivery_note_erp, cliente, orden_venta, codigo_producto, descripcion, lote, cantidad, fecha_entrega, no_guia, destino, estado FROM etiquetas_producto_terminado WHERE id = %s", (item_id,))
                        r = cur.fetchone()
                        if r:
                            datos = {
                                'id_entrega': r[0], 'delivery_note_erp': r[1] or "", 'cliente': r[2], 'orden_venta': r[3],
                                'codigo_producto': r[4], 'descripcion': r[5], 'lote': r[6], 'cantidad': r[7],
                                'fecha_entrega': r[8], 'no_guia': r[9] or "", 'destino': r[10] or "", 'estado': r[11] or ""
                            }
                            img = self.render_etiqueta_pt(datos)
                            temp_img_path = f"temp_pt_{idx}.png"
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

        messagebox.showinfo("Exportado", f"Etiquetas PT PDF guardadas en:\n{filepath}")

    def eliminar_registro_pt(self):
        """Elimina de la base de datos las etiquetas PT seleccionadas."""
        selected = self.tree_pt.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione al menos un registro para eliminar.")
            return

        cant_seleccionados = len(selected)
        confirm = messagebox.askyesno("Eliminar Seleccionados", f"¿Está seguro de eliminar {cant_seleccionados} registro(s) seleccionado(s)?")
        if confirm:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        for item in selected:
                            item_id = self.tree_pt.item(item)['values'][0]
                            cur.execute("DELETE FROM etiquetas_producto_terminado WHERE id = %s", (item_id,))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Se eliminaron {cant_seleccionados} registro(s) correctamente.")
                    self.buscar_registros_pt()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudieron eliminar los registros:\n{e}")
                finally:
                    conn.close()