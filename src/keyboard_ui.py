"""
Interfaz visual del teclado virtual: cálculo de las 10 teclas sobre el
frame de video y su dibujo (con resaltado de selección/sugerencias).
"""
import cv2

from . import config


def calcular_teclas(w):
    """Devuelve la lista de rectángulos (x1, y1, x2, y2) de las 10 teclas
    distribuidas uniformemente sobre un ancho de frame `w`."""
    ancho_tecla = w / len(config.PALABRAS)
    teclas = []
    for i in range(len(config.PALABRAS)):
        x1, x2 = int(i * ancho_tecla), int((i + 1) * ancho_tecla)
        teclas.append((x1, 0, x2, config.ALTO_TECLA))
    return teclas


def dibujar_teclado(frame, teclas, resaltar=None, sugeridas=None):
    """Dibuja las teclas sobre `frame`.

    Parameters
    ----------
    resaltar : int | None
        Índice de la tecla actualmente bajo el dedo (se rellena de color).
    sugeridas : list[str] | None
        Palabras sugeridas por el grafo de predicción (se marcan con
        borde amarillo).
    """
    sugeridas = sugeridas or []
    for i, (x1, y1, x2, y2) in enumerate(teclas):
        color = config.COLORES[i]
        if resaltar == i:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        else:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            if config.PALABRAS[i] in sugeridas:
                cv2.rectangle(frame, (x1 + 3, y1 + 3), (x2 - 3, y2 - 3), (0, 255, 255), 3)
        cv2.putText(
            frame, config.PALABRAS[i], (x1 + 8, y2 - 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (255, 255, 255) if resaltar == i else color, 2,
        )
