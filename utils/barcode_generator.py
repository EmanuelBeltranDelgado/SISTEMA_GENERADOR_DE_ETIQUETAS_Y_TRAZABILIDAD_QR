import io
import barcode
from barcode.writer import ImageWriter
from PIL import Image

class BarcodeGenerator:
    @staticmethod
    def generar_codigo_barras(valor: str) -> Image.Image:
        """
        Genera una imagen PIL del código de barras en formato Code128 a partir de un texto.
        :param valor: Texto o folio a codificar (ej. P/N).
        :return: Objeto Image.Image de PIL con las barras dibujadas.
        """
        if not valor:
            valor = "N/A"
            
        # Opciones de renderizado para eliminar márgenes y texto automático
        # (ya que el texto P/N lo dibujamos centrado de forma personalizada)
        options = {
            'write_text': False,
            'module_height': 12.0,
            'module_width': 0.2,
            'quiet_zone': 1.0
        }
        
        code128 = barcode.get('code128', str(valor), writer=ImageWriter())
        buffer = io.BytesIO()
        code128.write(buffer, options=options)
        buffer.seek(0)
        
        img = Image.open(buffer)
        return img.convert("RGBA")