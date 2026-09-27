"""
Cálculos geométricos usados para reconocer la postura de control "L"
a partir de los landmarks de MediaPipe Pose.
"""
import math

import numpy as np

from . import config


def angulo_articular(a, b, c):
    """Ángulo (en grados) en el vértice b, formado por los segmentos a-b y c-b."""
    v1 = np.array([a[0] - b[0], a[1] - b[1]])
    v2 = np.array([c[0] - b[0], c[1] - b[1]])
    cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return math.degrees(math.acos(np.clip(cos_a, -1, 1)))


def es_postura_L(hombro, codo, muneca, ancho_ref):
    """
    Determina si el brazo forma una "L": codo ~90°, brazo (hombro-codo)
    horizontal y antebrazo (codo-muñeca) vertical hacia arriba.

    Parameters
    ----------
    hombro, codo, muneca : tuple(float, float)
        Coordenadas (x, y) en píxeles de cada articulación.
    ancho_ref : float
        Ancho de hombros en píxeles, usado como referencia de escala.
    """
    ang = angulo_articular(hombro, codo, muneca)
    brazo_horizontal = abs(hombro[1] - codo[1]) < config.TOL_HORIZONTAL * ancho_ref
    antebrazo_vertical = (
        abs(codo[0] - muneca[0]) < config.TOL_VERTICAL * ancho_ref
        and muneca[1] < codo[1]
    )
    dentro_rango = config.ANGULO_CODO_OBJ[0] <= ang <= config.ANGULO_CODO_OBJ[1]
    return dentro_rango and brazo_horizontal and antebrazo_vertical
