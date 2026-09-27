"""
Configuración global del sistema.

Centraliza el vocabulario del teclado, la paleta de colores y todos los
umbrales/parámetros que antes estaban dispersos como variables sueltas
en el notebook original.
"""

# ---------------------------------------------------------------------------
# Vocabulario del teclado virtual (10 teclas = 10 nodos del grafo)
# ---------------------------------------------------------------------------
PALABRAS = ["HOLA", "SI", "NO", "TENGO", "SED", "HAMBRE",
            "GRACIAS", "AYUDA", "DOLOR", "ADIOS"]

# Colores BGR (formato OpenCV) asociados a cada tecla, en el mismo orden
# que PALABRAS.
COLORES = [
    (66, 133, 244), (52, 168, 83), (234, 67, 53), (251, 188, 4), (154, 42, 152),
    (0, 172, 193), (255, 109, 0), (121, 85, 72), (96, 125, 139), (233, 30, 99),
]

# ---------------------------------------------------------------------------
# Geometría del teclado en pantalla
# ---------------------------------------------------------------------------
ALTO_TECLA = 90  # alto en px de la franja del teclado

# ---------------------------------------------------------------------------
# Selección por permanencia (dwell time)
# ---------------------------------------------------------------------------
DWELL_SEG = 3.0  # segundos de permanencia del índice para confirmar selección

# ---------------------------------------------------------------------------
# Detección de la postura de control "L"
# ---------------------------------------------------------------------------
ANGULO_CODO_OBJ = (70, 110)     # rango aceptado para "codo en L" (90° ± 20°)
TOL_HORIZONTAL = 0.35           # tolerancia (fracción del ancho de hombros)
TOL_VERTICAL = 0.35             # ídem, para el antebrazo
FRAMES_CONFIRMACION_L = 8       # histéresis: frames consecutivos para confirmar

# ---------------------------------------------------------------------------
# Autocompletado (grafo de predicción)
# ---------------------------------------------------------------------------
TOP_K_SUGERENCIAS = 2

# Conjunto semilla de transiciones típicas ("conocimiento previo" del
# vocabulario elegido, antes de que el usuario use el sistema).
SEMILLA_TRANSICIONES = {
    ("TENGO", "SED"): 3,
    ("TENGO", "HAMBRE"): 3,
    ("TENGO", "DOLOR"): 2,
    ("HOLA", "TENGO"): 1,
    ("SI", "GRACIAS"): 1,
    ("NO", "GRACIAS"): 1,
    ("AYUDA", "DOLOR"): 1,
    ("GRACIAS", "ADIOS"): 2,
}
