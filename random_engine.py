import random

def seleccionar_contenido(contenido):
    if not contenido:
        return None

    return random.choice(contenido)