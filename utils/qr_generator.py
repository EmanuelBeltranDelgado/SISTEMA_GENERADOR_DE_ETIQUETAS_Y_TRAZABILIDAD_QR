"""
===============================================================================
MÓDULO GENERADOR DE CÓDIGOS QR
===============================================================================
Clase utilitaria para la creación y generación gráfica de códigos QR estandarizados
usando Pillow y qrcode.
===============================================================================
"""

import qrcode

# =============================================================================
# --- MOTOR DE GENERACIÓN DE CÓDIGOS QR ---
# =============================================================================
class QRGenerator:
    """
    Clase utilitaria para compilar datos alfanuméricos y generar imágenes QR estandarizadas.
    """
    @staticmethod
    def make(data, box_size=8):
        """
        Crea una imagen PIL del código QR con los datos proporcionados.
        
        :param data: Texto o cadena formateada a codificar en el QR.
        :param box_size: Tamaño en píxeles de cada cuadro (módulo) del código QR.
        :return: Objeto PIL.Image en formato RGB.
        """
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M, # Corrección de errores ~15%
            box_size=box_size,
            border=2
        )
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert("RGB")