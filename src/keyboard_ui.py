"""
Interfaz visual del teclado virtual: cálculo de las 10 teclas sobre el
frame de video y su dibujo (con resaltado de selección/sugerencias).
"""
import cv2

from . import config


def calcular_teclas(w):
    """Devuelve la lista de rectángulos (x1, y1, x2, y2) de las 10 teclas
    en disposición 2x5 (2 filas, 5 columnas)."""
    espaciado = 10
    cols, filas = 5, 2
    ancho_disponible = w - (espaciado * (cols + 1))
    ancho_tecla = ancho_disponible / cols
    teclas = []
    for i in range(len(config.PALABRAS)):
        fila = i // cols
        col = i % cols
        x1 = int(espaciado + col * (ancho_tecla + espaciado))
        x2 = int(x1 + ancho_tecla)
        y1 = int(fila * (config.ALTO_TECLA + espaciado))
        y2 = int(y1 + config.ALTO_TECLA)
        teclas.append((x1, y1, x2, y2))
    return teclas


def dibujar_teclado(frame, teclas, resaltar=None, sugeridas=None, contador_regresiva=None):
    """Dibuja las teclas sobre `frame`.

    Parameters
    ----------
    resaltar : int | None
        Índice de la tecla actualmente bajo el dedo (se rellena de color).
    sugeridas : list[str] | None
        Palabras sugeridas por el grafo de predicción (se marcan con
        borde amarillo).
    contador_regresiva : dict | None
        Dict con {tecla_idx: segundos_restantes} para mostrar cuenta regresiva.
    """
    sugeridas = sugeridas or []
    contador_regresiva = contador_regresiva or {}
    for i, (x1, y1, x2, y2) in enumerate(teclas):
        color = config.COLORES[i]
        if resaltar == i:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        else:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            if config.PALABRAS[i] in sugeridas:
                cv2.rectangle(frame, (x1 + 3, y1 + 3), (x2 - 3, y2 - 3), (0, 255, 255), 3)

        centro_x = (x1 + x2) // 2
        centro_y = (y1 + y2) // 2

        texto_principal = config.PALABRAS[i]
        text_size, _ = cv2.getTextSize(texto_principal, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        x_texto = centro_x - text_size[0] // 2
        y_texto = centro_y - 8

        cv2.putText(
            frame, texto_principal, (x_texto, y_texto),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (255, 255, 255) if resaltar == i else color, 2,
        )

        if i in contador_regresiva:
            seg_restantes = contador_regresiva[i]
            tiempo_txt = f"{seg_restantes:.1f}"
            text_size, _ = cv2.getTextSize(tiempo_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 3)
            x_tiempo = centro_x - text_size[0] // 2
            y_tiempo = centro_y + 16
            cv2.putText(
                frame, tiempo_txt, (x_tiempo, y_tiempo),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 3,
            )
