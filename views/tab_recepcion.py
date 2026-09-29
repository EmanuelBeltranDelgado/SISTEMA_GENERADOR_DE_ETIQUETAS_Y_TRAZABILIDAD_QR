"""
===============================================================================
MÓDULO PESTAÑAS: RECEPCIÓN DE MATERIALES
===============================================================================
Gestiona la generación de etiquetas de entrada de mercancía, consulta, consumo 
de stock, reubicación y exportación a PNG/PDF.
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
from utils.validators import es_numero_valido

class TabRecepcion:
    def __init__(self, main_app, tab_generar, tab_consultar):
        self.main_app = main_app
        self.root = main_app.root
        self.tab_generar = tab_generar
        self.tab_consultar = tab_consultar

        # ---------------------------------------------------------------------
        # VARIABLES DE CONTROL DE TKINTER (Módulo: Recepciones)
        # ---------------------------------------------------------------------
        self.var_id_recepcion = tk.StringVar()
        self.var_id_recepcion_erpnext = tk.StringVar(value="")
        self.var_f_recepcion = tk.StringVar(value=datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_proveedor = tk.StringVar(value="")
        self.var_PN = tk.StringVar(value="")
        self.var_descripcion = tk.StringVar(value="")
        self.var_cantidad = tk.StringVar(value="")
        self.var_unidad = tk.StringVar(value="pz")
        self.var_lote = tk.StringVar(value="")
        self.var_f_fabricacion = tk.StringVar(value="")
        self.var_f_caducidad = tk.StringVar(value="")
        self.var_ubicacion = tk.StringVar(value="")
        self.var_almacen_erp = tk.StringVar(value="")
        self.var_estado = tk.StringVar(value="LIBERADO")
        self.var_caract_esp = tk.StringVar(value="")
        self.var_tipo_ingreso = tk.StringVar(value="Material comprado")
        self.var_select_all = tk.BooleanVar(value=False)

        self.img_etiqueta_pil = None
        self.generar_nuevo_id()

        # Inicialización de vistas
        self.setup_tab_generar()
        self.setup_tab_consultar()

    def generar_nuevo_id(self):
        """Genera un folio único con la sintaxis REC-AAAAMMDD-HHMMSS para Recepciones."""
        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.var_id_recepcion.set(f"REC-{now_str}")

    def limpiar_campos(self):
        """Limpia los campos del formulario de generación de etiquetas de Recepción."""
        self.generar_nuevo_id()
        self.var_id_recepcion_erpnext.set("")
        self.var_f_recepcion.set(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.var_proveedor.set("")
        self.var_PN.set("")
        self.var_descripcion.set("")
        self.var_cantidad.set("")
        self.var_unidad.set("pz")
        self.var_lote.set("")
        self.var_f_fabricacion.set("")
        self.var_f_caducidad.set("")
        self.var_ubicacion.set("")
        self.var_almacen_erp.set("")
        self.var_estado.set("LIBERADO")
        self.var_caract_esp.set("")
        self.var_tipo_ingreso.set("Material comprado")
        
        self.img_etiqueta_pil = None
        self.lbl_preview.config(image="", text="Captura los datos y pulsa GENERAR ETIQUETA")
        self.lbl_preview.image = None

    # =========================================================================
    # --- MÓDULO 1: RECEPCIONES (GENERACIÓN Y RENDERIZADO) ---
    # =========================================================================
    def setup_tab_generar(self):
        """Construye la UI para la captura de datos y vista previa de Recepción."""
        panel_izq = ttk.Frame(self.tab_generar, padding=15)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(panel_izq, text="Datos de recepción", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        vcmd = (self.root.register(es_numero_valido), '%P')

        fields = [
            ("ID recepción *", self.var_id_recepcion, True, False),
            ("ID Recepción ERPnext *", self.var_id_recepcion_erpnext, False, False),
            ("Fecha recepción *", self.var_f_recepcion, False, False),
            ("Proveedor *", self.var_proveedor, False, False),
            ("P/N *", self.var_PN, False, False),
            ("Descripción *", self.var_descripcion, False, False),
            ("Lote *", self.var_lote, False, False),
            ("Fecha fabricación *", self.var_f_fabricacion, False, False),
            ("Fecha caducidad *", self.var_f_caducidad, False, False),
            ("Ubicación *", self.var_ubicacion, False, False),
            ("Almacén ERPNext *", self.var_almacen_erp, False, False),
            ("Características Especiales\n(Opcional)", self.var_caract_esp, False, False),
        ]

        row = 1
        for label_text, var, readonly, es_num in fields:
            ttk.Label(panel_izq, text=label_text).grid(row=row, column=0, sticky="w", pady=3)
            state = "readonly" if readonly else "normal"
            if es_num:
                ttk.Entry(panel_izq, textvariable=var, state=state, width=28, validate="key", validatecommand=vcmd).grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
            else:
                ttk.Entry(panel_izq, textvariable=var, state=state, width=28).grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
            row += 1

        ttk.Label(panel_izq, text="Tipo de ingreso *").grid(row=row, column=0, sticky="w", pady=3)
        cb_tipo_ingreso = ttk.Combobox(panel_izq, textvariable=self.var_tipo_ingreso, width=26, state="readonly")
        cb_tipo_ingreso['values'] = ("Material comprado", "Material consignado", "Material IMEX")
        cb_tipo_ingreso.grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        row += 1

        ttk.Label(panel_izq, text="Cantidad *").grid(row=row, column=0, sticky="w", pady=3)
        frame_cant = ttk.Frame(panel_izq)
        frame_cant.grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        
        ttk.Entry(frame_cant, textvariable=self.var_cantidad, width=15, validate="key", validatecommand=vcmd).pack(side=tk.LEFT, padx=(0, 5))
        cb_unidad = ttk.Combobox(frame_cant, textvariable=self.var_unidad, width=8, state="readonly")
        cb_unidad['values'] = ("pz", "kg", "lts", "oz", "mtr", "gal", "ft", "paq")
        cb_unidad.pack(side=tk.LEFT)
        row += 1

        ttk.Label(panel_izq, text="Estado *").grid(row=row, column=0, sticky="w", pady=3)
        cb_estado = ttk.Combobox(panel_izq, textvariable=self.var_estado, width=26, state="readonly")
        cb_estado['values'] = ("CUARENTENA", "LIBERADO", "BLOQUEADO")
        cb_estado.grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        row += 1

        frame_botones_generar = ttk.Frame(panel_izq)
        frame_botones_generar.grid(row=row, column=0, columnspan=2, pady=15, sticky="ew")

        btn_generar = ttk.Button(frame_botones_generar, text="GENERAR ETIQUETA", style="Primary.TButton", command=self.accion_generar_etiqueta)
        btn_generar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_limpiar = ttk.Button(frame_botones_generar, text="LIMPIAR CAMPOS", style="Secondary.TButton", command=self.limpiar_campos)
        btn_limpiar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Panel Derecho: Vista previa de la etiqueta estandarizada
        panel_der = ttk.Frame(self.tab_generar, padding=15)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.card_preview = tk.Frame(panel_der, bg="#f0f0f0", bd=1, relief="solid", highlightthickness=1, highlightbackground="#dcdfe6")
        self.card_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        lbl_titulo_preview = tk.Label(self.card_preview, text="Vista previa 60 × 40 mm", font=("Segoe UI", 9), bg="#f0f0f0", fg="#333333")
        lbl_titulo_preview.pack(anchor="nw", padx=8, pady=8)

        self.lbl_preview = tk.Label(self.card_preview, text="Captura los datos y pulsa GENERAR ETIQUETA", font=("Segoe UI", 10), bg="#f0f0f0", fg="#000000")
        self.lbl_preview.pack(anchor="center", expand=True)

    def render_etiqueta(self, datos):
        """
        Dibuja con Pillow la maquetación física de la etiqueta de Recepción (Proporción 60x40 mm).
        Renders: Encabezados, textos de datos, código QR incrustado y borde.
        """
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='white')
        d = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arialbd.ttf", 22)
            medium_bold = ImageFont.truetype("arialbd.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 15)
        except:
            title_font = medium_bold = small_font = ImageFont.load_default()

        margin = 15

        d.text((margin + 100, margin), "Medusa Electronic S.A de C.V", fill='black', font=title_font)
        
        pn_texto = f"P/N : {datos['PN']}"
        d.text((margin, margin + 44), pn_texto[:28], fill='black', font=medium_bold)

        y = margin + 80
        spacing = 24
        
        items = [
            ("ID-REC", datos['id_recepcion']),
            ("ID-REC-ERP", datos['id_recepcion_erpnext']),
            ("CANT", datos['cantidad']),
            ("LOTE", datos['lote']),
            ("UBIC", datos['ubicacion']),
            ("EST", datos['estado']),
            ("TIPO-ING", datos['tipo_ingreso']),
            ("FECHA REC", datos['f_recepcion']),
            ("FECHA CAD", datos['f_caducidad'])
        ]

        if datos['caracteristicas_especiales']:
            items.insert(7, ("CAR-ESP", datos['caracteristicas_especiales']))

        for label, val in items:
            d.text((margin, y), f"{label}: {val}"[:28], fill='black', font=small_font)
            y += spacing

        qr_content = (f"ID-REC: {datos['id_recepcion']}\nID-REC-ERP: {datos['id_recepcion_erpnext']}\nCANT: {datos['cantidad']}\nLOTE: {datos['lote']}\nUBIC: {datos['ubicacion']}\nEST: {datos['estado']}\nTIPO-ING: {datos['tipo_ingreso']}\nFECHA-REC: {datos['f_recepcion']}\nFECHA-CAD: {datos['f_caducidad']}\nCAR-ESP: {datos['caracteristicas_especiales']}")
        
        qr_size = int(height * 0.42)
        qr_img = QRGenerator.make(qr_content, box_size=8)
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
        
        img.paste(qr_img, (width - qr_size - margin - 5, height - qr_size - margin - 20))

        if datos['descripcion']:
            d.text((margin, height - 25), datos['descripcion'][:35], fill='black', font=small_font)

        d.rectangle((0, 0, width - 1, height - 1), outline="black", width=3)
        return img

    def accion_generar_etiqueta(self):
        """Valida campos obligatorios, renderiza y guarda la recepción en DB."""
        cant_num = self.var_cantidad.get().strip()
        unidad = self.var_unidad.get().strip()
        cantidad_completa = f"{cant_num} {unidad}".strip()

        datos = {
            'id_recepcion': self.var_id_recepcion.get().strip(),
            'id_recepcion_erpnext': self.var_id_recepcion_erpnext.get().strip(),
            'f_recepcion': self.var_f_recepcion.get().strip(),
            'proveedor': self.var_proveedor.get().strip(),
            'PN': self.var_PN.get().strip(),
            'descripcion': self.var_descripcion.get().strip(),
            'cantidad': cantidad_completa,
            'lote': self.var_lote.get().strip(),
            'f_fabricacion': self.var_f_fabricacion.get().strip(),
            'f_caducidad': self.var_f_caducidad.get().strip(),
            'ubicacion': self.var_ubicacion.get().strip(),
            'almacen_erp': self.var_almacen_erp.get().strip(),
            'estado': self.var_estado.get().strip(),
            'caracteristicas_especiales': self.var_caract_esp.get().strip(),
            'tipo_ingreso': self.var_tipo_ingreso.get().strip()
        }

        if not cant_num:
            messagebox.showwarning("Campos Incompletos", "Por favor ingrese un valor numérico para la cantidad.")
            return

        campos_obligatorios = {k: v for k, v in datos.items() if k != 'caracteristicas_especiales'}
        for campo, valor in campos_obligatorios.items():
            if not valor:
                messagebox.showwarning("Campos Incompletos", f"Todos los campos son obligatorios. Falta llenar {campo.replace('_', ' ').title()}.")
                return

        self.img_etiqueta_pil = self.render_etiqueta(datos)
        img_tk = ImageTk.PhotoImage(self.img_etiqueta_pil.resize((500, 333)))
        self.lbl_preview.config(image=img_tk)
        self.lbl_preview.image = img_tk

        respuesta = messagebox.askyesno("Confirmar Registro", "¿Desea registrar esta recepción en la base de datos?")

        if respuesta:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO etiquetas_recepcion (
                                id_recepcion, id_recepcion_erpnext, fecha_recepcion, proveedor, pn, descripcion,
                                cantidad, lote, fecha_fabricacion, fecha_caducidad,
                                ubicacion, almacen_erpnext, estado, caracteristicas_especiales, tipo_ingreso
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, tuple(datos.values()))
                        conn.commit()
                    messagebox.showinfo("Éxito", "Recepción registrada correctamente.")
                    self.buscar_registros()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudo guardar la recepción:\n{e}")
                finally:
                    conn.close()

    # =========================================================================
    # --- MÓDULO 2: CONSULTA DE RECEPCIONES E INVENTARIO ---
    # =========================================================================
    def setup_tab_consultar(self):
        """Construye la UI para la consulta, filtrado e inventariado de Recepciones."""
        panel_top = ttk.Frame(self.tab_consultar, padding=10)
        panel_top.pack(fill=tk.X)

        ttk.Label(panel_top, text="Buscar por:").pack(side=tk.LEFT, padx=5)
        
        self.combo_criterio = ttk.Combobox(panel_top, state="readonly", values=[
            "Todos", "ID recepción", "ID Recepción ERPnext", "Fecha recepción", "Proveedor", "P/N", 
            "Descripción", "Cantidad", "Lote", "Fecha fabricación", 
            "Fecha caducidad", "Ubicación", "Almacén ERPNext", "Estado",
            "Características Especiales", "Tipo de Ingreso"
        ])
        self.combo_criterio.current(0)
        self.combo_criterio.pack(side=tk.LEFT, padx=5)

        self.var_busqueda = tk.StringVar()
        ttk.Entry(panel_top, textvariable=self.var_busqueda, width=25).pack(side=tk.LEFT, padx=5)

        btn_buscar = ttk.Button(panel_top, text="Buscar", style="Primary.TButton", command=self.buscar_registros)
        btn_buscar.pack(side=tk.LEFT, padx=5)

        chk_all = ttk.Checkbutton(
            panel_top, 
            text="Seleccionar Todo", 
            variable=self.var_select_all, 
            command=self.toggle_seleccionar_todo_rec
        )
        chk_all.pack(side=tk.RIGHT, padx=10)

        columns = ("db_id", "id_recepcion", "id_recepcion_erpnext", "pn", "lote", "cantidad", "estado", "ubicacion", "tipo_ingreso")
        self.tree = ttk.Treeview(self.tab_consultar, columns=columns, show="headings", selectmode="extended", height=12)
        
        self.tree.configure(displaycolumns=("id_recepcion", "id_recepcion_erpnext", "pn", "lote", "cantidad", "estado", "ubicacion", "tipo_ingreso"))

        self.tree.heading("id_recepcion", text="ID Recepción")
        self.tree.heading("id_recepcion_erpnext", text="ID ERPNext")
        self.tree.heading("pn", text="P/N")
        self.tree.heading("lote", text="Lote")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("ubicacion", text="Ubicación")
        self.tree.heading("tipo_ingreso", text="Tipo Ingreso")

        self.tree.column("id_recepcion", width=120)
        self.tree.column("id_recepcion_erpnext", width=120)
        self.tree.column("pn", width=100)
        self.tree.column("lote", width=90)
        self.tree.column("cantidad", width=80)
        self.tree.column("estado", width=90)
        self.tree.column("ubicacion", width=90)
        self.tree.column("tipo_ingreso", width=120)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", lambda event: self.mostrar_popup_etiqueta())

        panel_acciones = ttk.Frame(self.tab_consultar, padding=10)
        panel_acciones.pack(fill=tk.X)

        ttk.Button(panel_acciones, text="Ver Etiqueta", style="Primary.TButton", command=self.mostrar_popup_etiqueta).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Descontar / Consumir", style="Primary.TButton", command=self.popup_descontar_registro).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Cambiar Ubicación", style="Primary.TButton", command=self.popup_cambiar_ubicacion).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Descargar (PNG)", style="Secondary.TButton", command=self.exportar_png).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Descargar (PDF)", style="Secondary.TButton", command=self.exportar_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel_acciones, text="Eliminar Seleccionados", style="Danger.TButton", command=self.eliminar_registro).pack(side=tk.RIGHT, padx=5)

        self.buscar_registros()

    def toggle_seleccionar_todo_rec(self):
        """Selecciona o deselecciona todas las filas del Treeview de Recepciones."""
        if self.var_select_all.get():
            self.tree.selection_set(self.tree.get_children())
        else:
            self.tree.selection_remove(self.tree.get_children())

    def buscar_registros(self):
        """Consulta dinámicamente con SQL la tabla recepciones según el criterio indicado."""
        criterio = self.combo_criterio.get()
        valor = f"%{self.var_busqueda.get().strip()}%"

        mapa_columnas = {
            "ID recepción": "id_recepcion",
            "ID Recepción ERPnext": "id_recepcion_erpnext",
            "Fecha recepción": "fecha_recepcion",
            "Proveedor": "proveedor",
            "P/N": "pn",
            "Descripción": "descripcion",
            "Cantidad": "cantidad",
            "Lote": "lote",
            "Fecha fabricación": "fecha_fabricacion",
            "Fecha caducidad": "fecha_caducidad",
            "Ubicación": "ubicacion",
            "Almacén ERPNext": "almacen_erpnext",
            "Estado": "estado",
            "Características Especiales": "caracteristicas_especiales",
            "Tipo de Ingreso": "tipo_ingreso"
        }

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.var_select_all.set(False)

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if criterio == "Todos" or not self.var_busqueda.get().strip():
                        cur.execute("SELECT id, id_recepcion, id_recepcion_erpnext, pn, lote, cantidad, estado, ubicacion, tipo_ingreso FROM etiquetas_recepcion ORDER BY id DESC")
                    else:
                        col = mapa_columnas[criterio]
                        query = sql.SQL("SELECT id, id_recepcion, id_recepcion_erpnext, pn, lote, cantidad, estado, ubicacion, tipo_ingreso FROM etiquetas_recepcion WHERE {} ILIKE %s ORDER BY id DESC").format(sql.Identifier(col))
                        cur.execute(query, (valor,))
                    
                    rows = cur.fetchall()
                    for r in rows:
                        self.tree.insert("", tk.END, values=r)
            except Exception as e:
                messagebox.showerror("Error de Búsqueda", str(e))
            finally:
                conn.close()

    def _obtener_datos_seleccionados(self):
        """Método auxiliar que extrae y retorna la fila seleccionada en el Treeview."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un registro de la lista primero.")
            return None, None

        item_id = self.tree.item(selected[0])['values'][0]
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id_recepcion, id_recepcion_erpnext, fecha_recepcion, proveedor, pn, descripcion,
                               cantidad, lote, fecha_fabricacion, fecha_caducidad,
                               ubicacion, almacen_erpnext, estado, caracteristicas_especiales, tipo_ingreso 
                        FROM etiquetas_recepcion WHERE id = %s
                    """, (item_id,))
                    r = cur.fetchone()
                    datos = {
                        'id_recepcion': r[0], 'id_recepcion_erpnext': r[1] or "", 'f_recepcion': r[2], 'proveedor': r[3], 
                        'PN': r[4], 'descripcion': r[5], 'cantidad': r[6],
                        'lote': r[7], 'f_fabricacion': r[8], 'f_caducidad': r[9],
                        'ubicacion': r[10], 'almacen_erp': r[11], 'estado': r[12],
                        'caracteristicas_especiales': r[13] or "", 'tipo_ingreso': r[14] or ""
                    }
                    return item_id, datos
            finally:
                conn.close()
        return None, None

    def popup_cambiar_ubicacion(self):
        """Abre ventana emergente Toplevel para reubicar físicamente un material."""
        item_id, datos = self._obtener_datos_seleccionados()
        if not datos:
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Cambiar Ubicación - {datos['id_recepcion']}")
        popup.geometry("400x230")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        ttk.Label(popup, text=f"Cambiar Ubicación de {datos['id_recepcion']}", style="Header.TLabel").pack(pady=15)

        frame_fields = ttk.Frame(popup, padding=10)
        frame_fields.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame_fields, text="Ubicación actual:").grid(row=0, column=0, sticky="w", pady=6, padx=5)
        ttk.Label(frame_fields, text=datos['ubicacion'], font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", pady=6, padx=5)

        ttk.Label(frame_fields, text="Nueva ubicación:").grid(row=1, column=0, sticky="w", pady=6, padx=5)
        
        var_nueva_ubic = tk.StringVar(value="")
        entry_ubic = ttk.Entry(frame_fields, textvariable=var_nueva_ubic, width=20)
        entry_ubic.grid(row=1, column=1, sticky="w", pady=6, padx=5)
        entry_ubic.focus()

        def procesar_cambio_ubicacion():
            nueva_ubic = var_nueva_ubic.get().strip()
            if not nueva_ubic:
                messagebox.showwarning("Atención", "Ingrese la nueva ubicación.", parent=popup)
                return

            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE etiquetas_recepcion SET ubicacion = %s WHERE id = %s", (nueva_ubic, item_id))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Ubicación actualizada correctamente a '{nueva_ubic}'.", parent=popup)
                    popup.destroy()
                    self.buscar_registros()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudo actualizar la ubicación:\n{e}", parent=popup)
                finally:
                    conn.close()

        frame_btns = ttk.Frame(popup, padding=10)
        frame_btns.pack(fill=tk.X)

        ttk.Button(frame_btns, text="Guardar Ubicación", style="Primary.TButton", command=procesar_cambio_ubicacion).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(frame_btns, text="Cancelar", style="Secondary.TButton", command=popup.destroy).pack(side=tk.RIGHT, padx=5, expand=True)

    def popup_descontar_registro(self):
        """Abre ventana emergente Toplevel para descontar stock consumido en producción."""
        item_id, datos = self._obtener_datos_seleccionados()
        if not datos:
            return

        partes = datos['cantidad'].split(' ')
        try:
            cant_actual_num = float(partes[0])
            unidad_actual = partes[1] if len(partes) > 1 else ""
        except ValueError:
            cant_actual_num = 0.0
            unidad_actual = ""

        if datos['estado'] == "CONSUMIDO" or cant_actual_num <= 0:
            messagebox.showinfo("Registro Consumido", "Esta etiqueta ya se encuentra totalmente consumida (0 disponibles).")
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Descontar Stock - {datos['id_recepcion']}")
        popup.geometry("400x260")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        ttk.Label(popup, text=f"Descontar Stock de {datos['id_recepcion']}", style="Header.TLabel").pack(pady=15)

        frame_fields = ttk.Frame(popup, padding=10)
        frame_fields.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame_fields, text="Disponible actual:").grid(row=0, column=0, sticky="w", pady=6, padx=5)
        ttk.Label(frame_fields, text=f"{cant_actual_num} {unidad_actual}", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", pady=6, padx=5)

        ttk.Label(frame_fields, text="Cantidad a restar:").grid(row=1, column=0, sticky="w", pady=6, padx=5)
        
        var_a_restar = tk.StringVar(value="")
        vcmd = (self.root.register(es_numero_valido), '%P')
        entry_restar = ttk.Entry(frame_fields, textvariable=var_a_restar, width=15, validate="key", validatecommand=vcmd)
        entry_restar.grid(row=1, column=1, sticky="w", pady=6, padx=5)
        entry_restar.focus()

        def procesar_descuento():
            restar_str = var_a_restar.get().strip()
            if not restar_str:
                messagebox.showwarning("Atención", "Ingrese la cantidad a descontar.", parent=popup)
                return

            a_restar = float(restar_str)
            if a_restar <= 0:
                messagebox.showwarning("Atención", "La cantidad a restar debe ser mayor a 0.", parent=popup)
                return

            nueva_cant_num = cant_actual_num - a_restar

            if nueva_cant_num <= 0:
                nueva_cant_num = 0
                nuevo_estado = "CONSUMIDO"
            else:
                nuevo_estado = "EN STOCK" if datos['estado'] not in ("CUARENTENA", "BLOQUEADO") else datos['estado']

            nueva_cantidad_str = f"{int(nueva_cant_num) if nueva_cant_num.is_integer() else nueva_cant_num} {unidad_actual}".strip()

            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE etiquetas_recepcion SET cantidad = %s, estado = %s WHERE id = %s", (nueva_cantidad_str, nuevo_estado, item_id))
                        conn.commit()
                    
                    msg = f"Se restaron {a_restar} {unidad_actual}.\nNuevo Stock: {nueva_cantidad_str}\nNuevo Estado: {nuevo_estado}"
                    messagebox.showinfo("Stock Actualizado", msg, parent=popup)
                    popup.destroy()
                    self.buscar_registros()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudo actualizar el stock:\n{e}", parent=popup)
                finally:
                    conn.close()

        frame_btns = ttk.Frame(popup, padding=10)
        frame_btns.pack(fill=tk.X)

        ttk.Button(frame_btns, text="Aplicar Descuento", style="Primary.TButton", command=procesar_descuento).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(frame_btns, text="Cancelar", style="Secondary.TButton", command=popup.destroy).pack(side=tk.RIGHT, padx=5, expand=True)

    def mostrar_popup_etiqueta(self):
        """Despliega una ventana emergente para visualizar en alta resolución la etiqueta seleccionada."""
        item_id, datos = self._obtener_datos_seleccionados()
        if not datos:
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Vista Previa - {datos['id_recepcion']}")
        popup.geometry("800x600")
        popup.configure(bg="#f4f6f8")
        popup.resizable(False, False)
        popup.grab_set()

        img_pil = self.render_etiqueta(datos)
        img_tk = ImageTk.PhotoImage(img_pil.resize((720, 480)))

        lbl_img = ttk.Label(popup, image=img_tk, background="#f4f6f8")
        lbl_img.image = img_tk
        lbl_img.pack(expand=True, pady=15)

        ttk.Button(popup, text="Cerrar", style="Secondary.TButton", command=popup.destroy).pack(pady=(0, 15))

    def exportar_png(self):
        """Guarda la etiqueta individual seleccionada como imagen en formato PNG."""
        item_id, datos = self._obtener_datos_seleccionados()
        if datos:
            filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")], initialfile=f"Etiqueta_{datos['id_recepcion']}.png")
            if filepath:
                img = self.render_etiqueta(datos)
                img.save(filepath)
                messagebox.showinfo("Exportado", f"Etiqueta guardada en:\n{filepath}")

    def exportar_pdf(self):
        """Genera un archivo PDF con la etiqueta o lista de etiquetas seleccionadas en dimensiones 60x40 mm."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Atención", "Seleccione al menos un registro de la lista.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"Etiquetas_Recepcion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
                        item_id = self.tree.item(item)['values'][0]
                        cur.execute("""
                            SELECT id_recepcion, id_recepcion_erpnext, fecha_recepcion, proveedor, pn, descripcion,
                                   cantidad, lote, fecha_fabricacion, fecha_caducidad,
                                   ubicacion, almacen_erpnext, estado, caracteristicas_especiales, tipo_ingreso 
                            FROM etiquetas_recepcion WHERE id = %s
                        """, (item_id,))
                        r = cur.fetchone()
                        if r:
                            datos = {
                                'id_recepcion': r[0], 'id_recepcion_erpnext': r[1] or "", 'f_recepcion': r[2], 'proveedor': r[3], 
                                'PN': r[4], 'descripcion': r[5], 'cantidad': r[6],
                                'lote': r[7], 'f_fabricacion': r[8], 'f_caducidad': r[9],
                                'ubicacion': r[10], 'almacen_erp': r[11], 'estado': r[12],
                                'caracteristicas_especiales': r[13] or "", 'tipo_ingreso': r[14] or ""
                            }
                            img = self.render_etiqueta(datos)
                            temp_img_path = f"temp_rec_{idx}.png"
                            img.save(temp_img_path)
                            temp_files.append(temp_img_path)
                            c.drawImage(temp_img_path, 0, 0, width=60*mm, height=40*mm)
                            c.showPage()
                c.save()
            finally:
                conn.close()

        # Limpieza de archivos temporales de imagen
        for tmp in temp_files:
            if os.path.exists(tmp):
                os.remove(tmp)

        messagebox.showinfo("Exportado", f"Etiquetas PDF guardadas en:\n{filepath}")

    def eliminar_registro(self):
        """Elimina físicamente los registros seleccionados de la base de datos previa confirmación."""
        selected = self.tree.selection()
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
                            item_id = self.tree.item(item)['values'][0]
                            cur.execute("DELETE FROM etiquetas_recepcion WHERE id = %s", (item_id,))
                        conn.commit()
                    messagebox.showinfo("Éxito", f"Se eliminaron {cant_seleccionados} registro(s) correctamente.")
                    self.buscar_registros()
                except Exception as e:
                    messagebox.showerror("Error SQL", f"No se pudieron eliminar los registros:\n{e}")
                finally:
                    conn.close()