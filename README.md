# Teclado gestual + análisis de grafos de interacción

Proyecto integrador — *Aplicaciones de Datos en Redes Complejas*

## Objetivo

Diseñar un sistema analítico–computacional en tiempo real (sobre video)
que integre:

1. Detección de postura corporal (MediaPipe Pose) y de manos (MediaPipe
   Hands) simultáneamente.
2. Reconocimiento de la postura **"L"** de cada brazo como comando de
   control: brazo izquierdo activa la grabación de un mensaje, brazo
   derecho la finaliza y lo muestra.
3. Un teclado virtual de 10 teclas (palabras) seleccionables por
   permanencia (*dwell time* ≥ 3 s) del dedo índice.
4. Modelado de cada mensaje como un **grafo dirigido y ponderado**:
   teclas = nodos, transiciones entre selecciones consecutivas = aristas.
5. **Autocompletado en tiempo real**, a partir de ese mismo grafo (p. ej.
   tras seleccionar `TENGO`, sugerir `SED` o `HAMBRE`).
6. Métricas topológicas, centralidad, resiliencia estructural, evolución
   temporal, comunidades y un proceso de difusión sobre el grafo de
   interacción resultante.

## Arquitectura propuesta

El proyecto original (un notebook único de Colab) fue reorganizado en un
paquete modular para separar responsabilidades y permitir reutilizar cada
componente de forma independiente (por ejemplo, correr el análisis de
grafos sin necesitar OpenCV/MediaPipe instalados, o generar datos de
prueba sin filmar un video):

```
teclado_gestual_grafos/
├── main.ipynb              # notebook de orquestación (punto de entrada)
├── requirements.txt
├── README.md
├── src/
│   ├── config.py            # vocabulario, colores, umbrales, grafo semilla
│   ├── geometry.py           # ángulos articulares y detección de postura "L"
│   ├── keyboard_ui.py         # dibujo del teclado virtual sobre el frame
│   ├── prediction_graph.py    # grafo de autocompletado (bigrama)
│   ├── vision_pipeline.py     # detección con MediaPipe sobre video real
│   ├── data_simulation.py     # generación de datos simulados (sin video)
│   ├── graph_analysis.py      # métricas, centralidad, resiliencia,
│   │                          # comunidades, difusión
│   └── visualization.py       # figuras (matplotlib) guardadas en outputs/
├── data/                    # datos de sesión (simulados o exportados)
├── outputs/                 # grafo agregado, evolución, centralidades, video
└── tests/
    └── test_graph_analysis.py
```

**Flujo de datos:**

```
video real ──► vision_pipeline.procesar_video ──┐
                                                 ├──► mensajes, grafos_sesion,
datos simulados ──► data_simulation.simular_sesiones ──┘   log_eventos, log_selecciones
                                                             │
                                                             ▼
                                              graph_analysis (métricas, centralidad,
                                              resiliencia, comunidades, difusión)
                                                             │
                                                             ▼
                                              visualization (PNG en outputs/)
```

`vision_pipeline` y `data_simulation` son intercambiables: ambos producen
la misma estructura de datos, por lo que `graph_analysis` y
`visualization` operan igual sobre datos reales o simulados. Esto permite
ejecutar y evaluar todo el pipeline de análisis de grafos sin depender de
una filmación real ni de las dependencias de visión.

### Decisiones metodológicas

- **MediaPipe Pose + Hands** en vez de MoveNet u OpenPose: ambos corren en
  CPU en tiempo casi real, comparten el mismo framework (`mp.solutions`) y
  permiten reutilizar patrones ya validados. MoveNet no incluye manos, y
  OpenPose es más pesado de instalar.
- **Grafo dirigido y ponderado** (`nx.DiGraph`): el orden de las
  transiciones importa (A→B ≠ B→A en un mensaje) y el peso captura cuántas
  veces se repite cada transición.
- **Postura "L"** como comando: geométricamente fácil de diferenciar
  (codo ≈ 90° + antebrazo vertical + brazo horizontal), evita falsos
  positivos con posturas naturales.
- **Dwell time de 3 s**: evita selecciones accidentales al pasar el dedo
  sobre el teclado camino a otra tecla.
- **Autocompletado basado en el propio grafo** (no en un LLM externo): las
  sugerencias son los sucesores de mayor peso del nodo activo — reutiliza
  la misma estructura que ya se necesita para el análisis topológico y
  hace que el teclado "aprenda" con cada selección confirmada.
- **Datos simulados como camino principal de entrega**: dado que el
  patrón de uso solo cobra sentido estadístico con múltiples sesiones
  reales, `data_simulation.py` genera sesiones sintéticas sesgadas por el
  propio grafo semilla (con una probabilidad de exploración), permitiendo
  ejercitar y validar todo el análisis sin depender de una filmación.

## Instalación

```bash
git clone <url-del-repositorio>
cd teclado_gestual_grafos
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

### Opción A — Notebook (recomendada)

```bash
jupyter notebook main.ipynb
```

Por defecto, el notebook usa `src.data_simulation` para generar una
sesión sintética y ejecuta todo el análisis de grafos y las
visualizaciones sin necesitar un video real. La sección 1.b del notebook
explica cómo reemplazar esa celda por `src.vision_pipeline.procesar_video`
para procesar un video real en su lugar.

### Opción B — Solo generar datos simulados y exportarlos

```bash
python -m src.data_simulation
```

Genera `data/eventos_simulados.csv` y `data/selecciones_simuladas.csv`.

### Opción C — Procesar un video real (requiere cámara/archivo de video)

```python
from src.vision_pipeline import procesar_video

resultado = procesar_video("mi_video.mp4", out_path="outputs/salida_teclado_gestual.mp4")
print(resultado.mensajes)
```

Requiere realizar, frente a la cámara: postura en **L** con el brazo
izquierdo (inicia grabación) → mover el índice sobre las teclas
manteniéndolo ≥ 3 s en cada una → postura en **L** con el brazo derecho
(finaliza grabación).

### Pruebas

```bash
python -m pytest tests/ -v
```

## Requisitos

Ver [`requirements.txt`](requirements.txt): `opencv-python`, `mediapipe`,
`numpy`, `pandas`, `networkx`, `matplotlib`, `jupyter`.

## Salidas generadas

- `outputs/grafo_teclado.png` — grafo agregado de transiciones entre teclas.
- `outputs/evolucion_grafo.png` — instantáneas de la red a medida que crece.
- `outputs/centralidades.png` — comparación de centralidad (PageRank) por tecla.
- `outputs/salida_teclado_gestual.mp4` — video anotado (solo con `vision_pipeline`).
- `data/*.csv` — logs de eventos y selecciones de la sesión.
