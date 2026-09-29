"""
===============================================================================
MÓDULO DE CONFIGURACIÓN Y CONEXIÓN A BASE DE DATOS POSTGRESQL
===============================================================================
Maneja la carga de variables de entorno desde el archivo .env, la apertura de
conexiones seguras y la inicialización de las tablas del esquema principal.
===============================================================================
"""

import os
import sys
from pathlib import Path
import psycopg2
from tkinter import messagebox
from dotenv import load_dotenv

# =============================================================================
# --- CONFIGURACIÓN DE CONEXIÓN A BASE DE DATOS POSTGRESQL ---
# =============================================================================
# Diccionario con los parámetros de conexión al servidor PostgreSQL.
# Modifica estas credenciales según las configuraciones de tu entorno/servidor.
if getattr(sys, 'frozen', False):
    # Si la aplicación se ejecuta compilada con PyInstaller
    base_dir = Path(sys._MEIPASS)
else:
    # Si la aplicación se ejecuta como script .py normal
    base_dir = Path(__file__).resolve().parent.parent

# Cargar .env desde la ruta resuelta
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    """
    Establece y retorna un objeto de conexión activo a PostgreSQL.
    En caso de falla, despliega una alerta visual de error (messagebox) y retorna None.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos:\n{e}")
        return None

def init_db():
    """
    Inicializa el esquema de la base de datos PostgreSQL creando las 4 tablas 
    principales en caso de que no existan previamente.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # -------------------------------------------------------------
                # TABLA 1: RECEPCIONES (Entrada de Material Comprado/Consignado/IMEX)
                # -------------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS etiquetas_recepcion (
                        id SERIAL PRIMARY KEY,
                        id_recepcion VARCHAR(100) UNIQUE,
                        id_recepcion_erpnext VARCHAR(100),
                        fecha_recepcion VARCHAR(50),
                        proveedor VARCHAR(150),
                        pn VARCHAR(100),
                        descripcion TEXT,
                        cantidad VARCHAR(50),
                        lote VARCHAR(100),
                        fecha_fabricacion VARCHAR(50),
                        fecha_caducidad VARCHAR(50),
                        ubicacion VARCHAR(100),
                        almacen_erpnext VARCHAR(100),
                        estado VARCHAR(50),
                        caracteristicas_especiales TEXT,
                        tipo_ingreso VARCHAR(100)
                    );
                """)

                # -------------------------------------------------------------
                # TABLA 2: PRODUCTO TERMINADO (Embarques y Órdenes de Venta)
                # -------------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS etiquetas_producto_terminado (
                        id SERIAL PRIMARY KEY,
                        id_entrega VARCHAR(100) UNIQUE,
                        delivery_note_erp VARCHAR(100),
                        cliente VARCHAR(150),
                        orden_venta VARCHAR(100),
                        codigo_producto VARCHAR(100),
                        descripcion TEXT,
                        lote VARCHAR(100),
                        cantidad VARCHAR(50),
                        fecha_entrega VARCHAR(50),
                        no_guia VARCHAR(100),
                        destino TEXT,
                        estado VARCHAR(50)
                    );
                """)

                # -------------------------------------------------------------
                # TABLA 3: TRAZABILIDAD QR PCB (Serialización Consecutiva de Placas)
                # -------------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS etiqueta_trazabilidad_qr_pcb (
                        id SERIAL PRIMARY KEY,
                        serial VARCHAR(100) UNIQUE,
                        work_order VARCHAR(100),
                        pn VARCHAR(100),
                        lote VARCHAR(100),
                        cantidad VARCHAR(50),
                        fecha VARCHAR(50)
                    );
                """)

                # -------------------------------------------------------------
                # TABLA 4: TRAZABILIDAD QR M-G-S (Muestras Master, Golden, Silver)
                # -------------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS etiqueta_trazabilidad_qr_gms (
                        id SERIAL PRIMARY KEY,
                        tipo VARCHAR(50),
                        id_medusa VARCHAR(100),
                        pn VARCHAR(100),
                        serial VARCHAR(100) UNIQUE,
                        fecha VARCHAR(50)
                    );
                """)
                conn.commit()
        except Exception as e:
            print("Error al inicializar la base de datos:", e)
        finally:
            conn.close()