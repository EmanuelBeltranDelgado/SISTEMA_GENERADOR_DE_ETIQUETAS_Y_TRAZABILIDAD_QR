"""
===============================================================================
MÓDULO DE ESTILOS VISUALES TTK
===============================================================================
Configura el tema general, colores corporativos, tipografías y comportamiento de 
botones y componentes gráficos ttk.
===============================================================================
"""

from tkinter import ttk

def setup_styles(root):
    """
    Aplica un tema corporativo moderno usando ttk.Style.
    Modifica colores, bordes, fuentes y respuestas a eventos (hover/active).
    """
    style = ttk.Style()
    style.theme_use('clam')

    bg_main = "#f4f6f8"
    bg_card = "#ffffff"
    text_dark = "#2c3e50"
    border_color = "#dcdfe6"

    style.configure("TFrame", background=bg_main)
    style.configure("Card.TFrame", background=bg_card, relief="flat")
    style.configure("TLabel", background=bg_main, foreground=text_dark, font=("Segoe UI", 9))
    style.configure("Header.TLabel", background=bg_main, foreground=text_dark, font=("Segoe UI", 11, "bold"))

    # Rediseño visual de las Pestañas (Tab View)
    style.configure("TNotebook", background=bg_main, borderwidth=0, tabmargins=[10, 5, 10, 0])
    style.layout("TNotebook.Tab", [
        ("Notebook.tab", {
            "sticky": "nswe",
            "children": [
                ("Notebook.padding", {
                    "side": "top",
                    "sticky": "nswe",
                    "children": [
                        ("Notebook.label", {"side": "top", "sticky": ""})
                    ]
                })
            ]
        })
    ])

    style.configure(
        "TNotebook.Tab", 
        background="#e2e8f0",          # Gris claro inactivo
        foreground="#475569",          # Texto oscuro
        font=("Segoe UI", 9, "bold"), 
        padding=[16, 8],
        borderwidth=0,
        focusthickness=0
    )
    
    style.map(
        "TNotebook.Tab", 
        background=[("selected", "#54A9C4"), ("active", "#cbd5e1")],
        foreground=[("selected", "#ffffff"), ("active", "#1e293b")],
        expand=[("selected", [0, 2, 0, 0])]
    )

    # Campos de texto y listas desplegables
    style.configure("TEntry", fieldbackground="white", bordercolor=border_color, padding=4)
    style.configure("TCombobox", fieldbackground="white", bordercolor=border_color, padding=4)

    # Botones Personalizados (Primary, Secondary, Danger)
    style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"), background="#54A9C4", foreground="white", borderwidth=0, focusthickness=0, padding=[12, 8])
    style.map("Primary.TButton", background=[("active", "#244B57"), ("pressed", "#1e40af")])

    style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#64748b", foreground="white", borderwidth=0, focusthickness=0, padding=[12, 8])
    style.map("Secondary.TButton", background=[("active", "#475569"), ("pressed", "#334155")])

    style.configure("Danger.TButton", font=("Segoe UI", 9, "bold"), background="#e11d48", foreground="white", borderwidth=0, focusthickness=0, padding=[12, 8])
    style.map("Danger.TButton", background=[("active", "#be123c"), ("pressed", "#9f1239")])

    # Estilo para Tablas (Treeview)
    style.configure("Treeview", background="white", fieldbackground="white", foreground=text_dark, rowheight=28, borderwidth=1, relief="solid")
    style.configure("Treeview.Heading", background="#475569", foreground="white", font=("Segoe UI", 9, "bold"), padding=5)
    style.map("Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "white")])
    return style