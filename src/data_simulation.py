"""
Generación de datos simulados.

Permite ejercitar todo el pipeline de análisis de grafos (sección 6 del
proyecto original) sin depender de una filmación real ni de las
dependencias de visión (OpenCV/MediaPipe). Se simulan sesiones de
"mensajes" como si un usuario real hubiera seleccionado teclas por dwell
time, usando el propio grafo semilla (`config.SEMILLA_TRANSICIONES`) como
sesgo: las transiciones ya conocidas son más probables, pero se deja una
probabilidad de exploración para que aparezcan aristas nuevas, igual que
haría un usuario real explorando el vocabulario.

Esto reproduce la misma estructura de datos (`mensajes`, `grafos_sesion`,
`log_eventos`, `log_selecciones`) que produce `vision_pipeline.procesar_video`,
por lo que `graph_analysis` y `visualization` pueden operar indistintamente
sobre datos simulados o datos reales.
"""
import random

import networkx as nx
import pandas as pd

from . import config
from .prediction_graph import construir_grafo_prediccion, reforzar_transicion


def _elegir_siguiente_palabra(g_pred, palabra_actual, prob_exploracion, rng):
    """Elige la siguiente palabra: con probabilidad `prob_exploracion` explora
    una palabra al azar; si no, sigue una arista existente de `g_pred`
    (ponderada por peso) o, si no hay ninguna, explora igual."""
    vecinos = list(g_pred.successors(palabra_actual)) if palabra_actual in g_pred else []
    if vecinos and rng.random() > prob_exploracion:
        pesos = [g_pred[palabra_actual][v]["weight"] for v in vecinos]
        return rng.choices(vecinos, weights=pesos, k=1)[0]
    candidatos = [p for p in config.PALABRAS if p != palabra_actual]
    return rng.choice(candidatos)


def simular_sesiones(n_mensajes=6, longitud_min=2, longitud_max=5,
                      prob_exploracion=0.35, semilla_aleatoria=42):
    """
    Genera `n_mensajes` mensajes simulados (secuencias de palabras) y
    construye las mismas estructuras que produciría el procesamiento de
    un video real.

    Returns
    -------
    dict con las llaves:
        mensajes         : list[list[str]]
        grafos_sesion    : list[nx.DiGraph]
        log_eventos      : list[dict]
        log_selecciones  : list[dict]
        g_pred           : nx.DiGraph (grafo de predicción, ya reforzado)
        df_eventos       : pd.DataFrame
        df_selecciones   : pd.DataFrame
    """
    rng = random.Random(semilla_aleatoria)
    g_pred = construir_grafo_prediccion()

    mensajes, grafos_sesion, log_eventos, log_selecciones = [], [], [], []
    frame_idx, fps_simulado = 0, 30
    dwell_frames = int(config.DWELL_SEG * fps_simulado)

    for num_sesion in range(1, n_mensajes + 1):
        longitud = rng.randint(longitud_min, longitud_max)
        primera_palabra = rng.choice(config.PALABRAS)
        sesion_actual = [primera_palabra]

        log_eventos.append({
            "frame": frame_idx, "tiempo_s": round(frame_idx / fps_simulado, 2),
            "evento": "INICIO_GRABACION (L izquierda)",
        })

        g_actual = nx.DiGraph()
        g_actual.add_nodes_from(config.PALABRAS)

        frame_idx += dwell_frames
        log_selecciones.append({
            "sesion": num_sesion, "frame": frame_idx,
            "tiempo_s": round(frame_idx / fps_simulado, 2), "mano": 0, "palabra": primera_palabra,
        })

        tecla_anterior = primera_palabra
        for _ in range(longitud - 1):
            palabra = _elegir_siguiente_palabra(g_pred, tecla_anterior, prob_exploracion, rng)
            sesion_actual.append(palabra)
            frame_idx += dwell_frames
            log_selecciones.append({
                "sesion": num_sesion, "frame": frame_idx,
                "tiempo_s": round(frame_idx / fps_simulado, 2), "mano": 0, "palabra": palabra,
            })
            if g_actual.has_edge(tecla_anterior, palabra):
                g_actual[tecla_anterior][palabra]["weight"] += 1
            else:
                g_actual.add_edge(tecla_anterior, palabra, weight=1)
            reforzar_transicion(g_pred, tecla_anterior, palabra)
            tecla_anterior = palabra

        frame_idx += int(0.5 * fps_simulado)  # pequeña pausa antes del cierre
        log_eventos.append({
            "frame": frame_idx, "tiempo_s": round(frame_idx / fps_simulado, 2),
            "evento": f"FIN_GRABACION (L derecha) -> mensaje: {' '.join(sesion_actual)}",
        })

        mensajes.append(sesion_actual)
        grafos_sesion.append(g_actual)
        frame_idx += fps_simulado  # separación entre sesiones

    return {
        "mensajes": mensajes,
        "grafos_sesion": grafos_sesion,
        "log_eventos": log_eventos,
        "log_selecciones": log_selecciones,
        "g_pred": g_pred,
        "df_eventos": pd.DataFrame(log_eventos),
        "df_selecciones": pd.DataFrame(log_selecciones),
    }


if __name__ == "__main__":
    # Genera un dataset simulado de ejemplo y lo guarda en data/,
    # para poder repartir el proyecto sin depender de un video real.
    resultado = simular_sesiones()
    resultado["df_eventos"].to_csv("data/eventos_simulados.csv", index=False)
    resultado["df_selecciones"].to_csv("data/selecciones_simuladas.csv", index=False)
    print(f"Mensajes simulados generados: {len(resultado['mensajes'])}")
    for i, m in enumerate(resultado["mensajes"], 1):
        print(f"  Mensaje {i}: {' '.join(m)}")
    print("Datos guardados en data/eventos_simulados.csv y data/selecciones_simuladas.csv")
