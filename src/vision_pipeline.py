"""
Pipeline de visión sobre video real: detección de postura (MediaPipe Pose)
y manos (MediaPipe Hands), reconocimiento de la postura de control "L" y
selección de teclas por permanencia (dwell time).

Este módulo requiere `opencv-python` y `mediapipe` instalados (ver
requirements.txt) y un archivo de video real como entrada. Para explorar
el análisis de grafos sin depender de una demostración filmada, usar
`src.data_simulation` en su lugar.
"""
from dataclasses import dataclass, field

import cv2
import networkx as nx
import pandas as pd

from . import config
from .geometry import es_postura_L
from .keyboard_ui import calcular_teclas, dibujar_teclado
from .prediction_graph import (
    construir_grafo_prediccion,
    reforzar_transicion,
    sugerir_siguientes,
)


@dataclass
class ResultadoSesion:
    """Resultado estructurado de procesar un video completo."""
    mensajes: list = field(default_factory=list)          # lista de listas de palabras
    grafos_sesion: list = field(default_factory=list)      # un nx.DiGraph por mensaje
    log_eventos: list = field(default_factory=list)        # eventos de inicio/fin
    log_selecciones: list = field(default_factory=list)    # cada tecla confirmada
    g_pred: "nx.DiGraph" = None                             # grafo de predicción final

    @property
    def df_eventos(self):
        return pd.DataFrame(self.log_eventos)

    @property
    def df_selecciones(self):
        return pd.DataFrame(self.log_selecciones)


def procesar_video(video_path, out_path="salida_teclado_gestual.mp4", mostrar_preview=False):
    """
    Procesa un video de principio a fin: detecta posturas "L" (inicio/fin
    de mensaje) y selecciones de teclas por dwell time, y anota el video
    de salida.

    Parameters
    ----------
    video_path : str
        Ruta al video de entrada (persona haciendo L-izquierda -> selección
        de teclas -> L-derecha).
    out_path : str
        Ruta donde se guarda el video anotado.
    mostrar_preview : bool
        Si True, muestra cada frame anotado con cv2.imshow (uso local,
        fuera de un notebook/Colab).

    Returns
    -------
    ResultadoSesion
    """
    import mediapipe as mp  # import diferido: solo se necesita en esta función

    mp_pose = mp.solutions.pose
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    pose = mp_pose.Pose(static_image_mode=False, model_complexity=1,
                         min_detection_confidence=0.5, min_tracking_confidence=0.5)
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2,
                            min_detection_confidence=0.5, min_tracking_confidence=0.5)

    g_pred = construir_grafo_prediccion()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {video_path}")

    fps_video = cap.get(cv2.CAP_PROP_FPS) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    teclas = calcular_teclas(w)

    out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps_video, (w, h))

    resultado = ResultadoSesion(g_pred=g_pred)

    grabando = False
    contador_L_izq, contador_L_der = 0, 0
    sesion_actual = []
    g_actual = None
    tecla_anterior = None
    sugerencias_actuales = []
    hover_inicio = {}
    tecla_confirmada_actual = {}
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        tiempo_seg = frame_idx / fps_video

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res_pose = pose.process(rgb)
        res_hands = hands.process(rgb)

        # ---------- Postura corporal: comandos L ----------
        if res_pose.pose_landmarks:
            lm = res_pose.pose_landmarks.landmark
            mp_drawing.draw_landmarks(
                frame, res_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
            )

            ancho_hombros = abs(
                lm[mp_pose.PoseLandmark.LEFT_SHOULDER].x - lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].x
            ) * w + 1e-6

            def punto(idx):
                return (lm[idx].x * w, lm[idx].y * h)

            l_izq = es_postura_L(punto(mp_pose.PoseLandmark.LEFT_SHOULDER),
                                  punto(mp_pose.PoseLandmark.LEFT_ELBOW),
                                  punto(mp_pose.PoseLandmark.LEFT_WRIST), ancho_hombros)
            l_der = es_postura_L(punto(mp_pose.PoseLandmark.RIGHT_SHOULDER),
                                  punto(mp_pose.PoseLandmark.RIGHT_ELBOW),
                                  punto(mp_pose.PoseLandmark.RIGHT_WRIST), ancho_hombros)

            contador_L_izq = contador_L_izq + 1 if l_izq else 0
            contador_L_der = contador_L_der + 1 if l_der else 0

            if contador_L_izq >= config.FRAMES_CONFIRMACION_L and not grabando:
                grabando = True
                sesion_actual = []
                g_actual = nx.DiGraph()
                g_actual.add_nodes_from(config.PALABRAS)
                tecla_anterior = None
                sugerencias_actuales = []
                resultado.log_eventos.append({
                    "frame": frame_idx, "tiempo_s": round(tiempo_seg, 2),
                    "evento": "INICIO_GRABACION (L izquierda)",
                })
                contador_L_izq = 0

            if contador_L_der >= config.FRAMES_CONFIRMACION_L and grabando:
                grabando = False
                resultado.mensajes.append(list(sesion_actual))
                resultado.grafos_sesion.append(g_actual)
                resultado.log_eventos.append({
                    "frame": frame_idx, "tiempo_s": round(tiempo_seg, 2),
                    "evento": f"FIN_GRABACION (L derecha) -> mensaje: {' '.join(sesion_actual)}",
                })
                contador_L_der = 0

        # ---------- Manos: selección de teclas por dwell time ----------
        resaltar_tecla = None
        if res_hands.multi_hand_landmarks:
            for mano_id, hand_lm in enumerate(res_hands.multi_hand_landmarks):
                mp_drawing.draw_landmarks(
                    frame, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )
                punta = hand_lm.landmark[8]  # punta del índice
                xi, yi = int(punta.x * w), int(punta.y * h)
                cv2.circle(frame, (xi, yi), 8, (255, 255, 255), -1)

                tecla_idx = next(
                    (i for i, (x1, y1, x2, y2) in enumerate(teclas) if x1 <= xi < x2 and y1 <= yi < y2),
                    None,
                )

                if grabando and tecla_idx is not None:
                    resaltar_tecla = tecla_idx
                    if hover_inicio.get(mano_id, (None, None))[0] != tecla_idx:
                        hover_inicio[mano_id] = (tecla_idx, tiempo_seg)
                        tecla_confirmada_actual[mano_id] = None
                    else:
                        _, t_inicio = hover_inicio[mano_id]
                        transcurrido = tiempo_seg - t_inicio
                        x1, y1, x2, y2 = teclas[tecla_idx]
                        frac = min(transcurrido / config.DWELL_SEG, 1.0)
                        cv2.rectangle(frame, (x1, y2 - 6), (x1 + int((x2 - x1) * frac), y2),
                                      (255, 255, 255), -1)

                        if transcurrido >= config.DWELL_SEG and tecla_confirmada_actual.get(mano_id) != tecla_idx:
                            palabra = config.PALABRAS[tecla_idx]
                            sesion_actual.append(palabra)
                            resultado.log_selecciones.append({
                                "sesion": len(resultado.mensajes) + 1, "frame": frame_idx,
                                "tiempo_s": round(tiempo_seg, 2), "mano": mano_id, "palabra": palabra,
                            })
                            if tecla_anterior is not None and tecla_anterior != palabra:
                                if g_actual.has_edge(tecla_anterior, palabra):
                                    g_actual[tecla_anterior][palabra]["weight"] += 1
                                else:
                                    g_actual.add_edge(tecla_anterior, palabra, weight=1)
                                reforzar_transicion(g_pred, tecla_anterior, palabra)
                            tecla_anterior = palabra
                            tecla_confirmada_actual[mano_id] = tecla_idx
                            sugerencias_actuales = sugerir_siguientes(g_pred, palabra)
                else:
                    hover_inicio[mano_id] = (tecla_idx, tiempo_seg)

        # ---------- Overlay ----------
        dibujar_teclado(frame, teclas, resaltar=resaltar_tecla,
                         sugeridas=sugerencias_actuales if grabando else [])
        estado_txt = "GRABANDO MENSAJE" if grabando else "En espera (postura L izquierda para iniciar)"
        color_estado = (0, 0, 255) if grabando else (0, 200, 0)
        cv2.rectangle(frame, (0, h - 64), (w, h), color_estado, -1)
        cv2.putText(frame, estado_txt + "  |  Mensaje actual: " + " ".join(sesion_actual),
                    (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        if grabando and sugerencias_actuales:
            cv2.putText(frame, "Sugerencia para continuar: " + " / ".join(sugerencias_actuales),
                        (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

        out.write(frame)
        if mostrar_preview:
            cv2.imshow("Teclado gestual", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_idx += 1

    cap.release()
    out.release()
    pose.close()
    hands.close()
    if mostrar_preview:
        cv2.destroyAllWindows()

    return resultado
