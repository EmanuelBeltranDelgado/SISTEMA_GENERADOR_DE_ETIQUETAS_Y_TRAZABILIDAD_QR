"""
===============================================================================
MÓDULO DE VALIDACIONES
===============================================================================
Contiene funciones auxiliares para validar las entradas numéricas y enteras 
dentro de las interfaces de usuario.
===============================================================================
"""

def es_numero_valido(val):
    """Valida que la entrada sea un número decimal (float) válido o campo vacío."""
    if val == "":
        return True
    try:
        float(val)
        return True
    except ValueError:
        return False

def es_entero_valido(val):
    """Valida que la entrada sea estrictamente un entero positivo (dígitos) o campo vacío."""
    if val == "":
        return True
    return val.isdigit()