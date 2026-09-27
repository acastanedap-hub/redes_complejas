"""
Prueba en tiempo real usando la webcam.

Ejecutar desde la raíz del repo:

    python probar_en_vivo.py

Se abrirá una ventana con el video de tu cámara y el teclado superpuesto.
Secuencia a realizar frente a la cámara:

    1) Postura en "L" con el brazo IZQUIERDO  -> inicia la grabación
       (codo ~90°, brazo horizontal, antebrazo vertical hacia arriba;
       mantenla ~0.3 s para que se confirme).
    2) Mueve el dedo índice sobre las teclas de la franja superior,
       quedándote quieto >= 3 s en cada una para confirmar la selección.
    3) Postura en "L" con el brazo DERECHO -> finaliza el mensaje y lo
       imprime en consola.

Presiona 'q' en la ventana de video para cortar la captura en cualquier
momento (por ejemplo, si la cámara no detecta bien la postura y quieres
reintentar).

Requiere cámara conectada y `opencv-python` + `mediapipe` instalados
(ver requirements.txt).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.vision_pipeline import procesar_video
from src import graph_analysis, visualization


def main():
    print("Abriendo la cámara (índice 0). Presiona 'q' en la ventana de video para salir.")
    print("Si tienes varias cámaras y no es la correcta, cambia CAMARA_INDEX abajo en este archivo.\n")

    CAMARA_INDEX = 0
    os.makedirs("outputs", exist_ok=True)

    resultado = procesar_video(
        CAMARA_INDEX,
        out_path="outputs/salida_teclado_gestual.mp4",
        mostrar_preview=True,
    )

    print(f"\nMensajes capturados: {len(resultado.mensajes)}")
    for i, m in enumerate(resultado.mensajes, 1):
        print(f"  Mensaje {i}: {' '.join(m)}")

    if not resultado.grafos_sesion:
        print("\nNo se registró ningún mensaje completo (¿se hicieron las posturas L "
              "de inicio y fin?). No hay grafo que analizar todavía.")
        return

    g = graph_analysis.unir_grafos(resultado.grafos_sesion)
    print(f"\nGrafo agregado: {g.number_of_nodes()} nodos, {g.number_of_edges()} aristas")

    ruta = visualization.plot_grafo_agregado(g)
    print(f"Visualización guardada en: {ruta}")
    print(f"Video anotado guardado en: outputs/salida_teclado_gestual.mp4")


if __name__ == "__main__":
    main()
