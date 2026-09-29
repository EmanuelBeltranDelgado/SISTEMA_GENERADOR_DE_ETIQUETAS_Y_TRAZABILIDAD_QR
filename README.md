# Sistema Generador de Etiquetas QR / Trazabilidad QR PCB

Sistema de interfaz gráfica desarrollado en Python con **Tkinter** y conectado a una base de datos **PostgreSQL**, diseñado para la gestión, control de inventarios, producto terminado y trazabilidad de tarjetas electrónicas (PCBs) y muestras en **Medusa Electronic S.A. de C.V.**

## Módulos Principales

1. **Recepción de Materiales**: Captura e impresión de etiquetas con código QR para material comprado, consignado o IMEX. Permite el control de estados (Liberado, Cuarentena, Bloqueado) y características especiales.
2. **Consulta e Inventario de Recepciones**: Filtrado dinámico, visualización de etiquetas, descuento/consumo de stock en tiempo real, cambio de ubicación y exportación a formatos PNG y PDF (dimensiones estándar 60x40 mm).
3. **Producto Terminado (PT)**: Generación, consulta y exportación de etiquetas de embarque asociadas a notas de entrega de ERPNext.
4. **Trazabilidad QR PCB**: Generación masiva y consecutiva de seriales numéricos de 9 dígitos optimizados para etiquetas ultra-compactas (40x15 mm) con distribución en cuadrícula para impresión en PDF. El lote debe ser generado apartir de la fecha de la cual se comenzo o se comenzara la produccion de las piezas.
5. **Trazabilidad QR M-G-S**: Registro y control de muestras patrón de referencia (**Master, Golden, Silver**).

## Requisitos Previos

* Python 3.8 o superior instalado en el equipo.
* Servidor de base de datos **PostgreSQL** activo y accesible en red.

## Instalación y Configuración

1. Clonar o descargar el repositorio del código fuente en tu entorno local.
2. Instalar las dependencias del sistema ejecutando el siguiente comando en tu terminal:

   ```bash
   pip install -r requirements.txt