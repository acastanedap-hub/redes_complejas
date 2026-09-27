"""
Teclado gestual + análisis de grafos de interacción.

Paquete modular que separa las responsabilidades del sistema original
(notebook monolítico de Colab) en componentes independientes:

- config              : parámetros globales (vocabulario, colores, umbrales)
- geometry            : cálculos geométricos para detección de posturas
- keyboard_ui         : dibujo del teclado virtual sobre el frame de video
- prediction_graph    : grafo de autocompletado (bigrama sobre el vocabulario)
- vision_pipeline     : detección con MediaPipe (Pose + Hands) sobre video real
- data_simulation     : generación de datos simulados (sin video/MediaPipe)
- graph_analysis      : métricas, centralidad, resiliencia, comunidades, difusión
- visualization       : generación de figuras (matplotlib) a partir de los grafos
"""
