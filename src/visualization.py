"""
Generación de figuras (matplotlib) a partir de los grafos de interacción:
grafo agregado, evolución temporal y centralidades. Todas las funciones
guardan la figura en `outputs/` y devuelven la ruta del archivo generado.
"""
import os

import matplotlib.pyplot as plt
import networkx as nx

from . import config

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")


def _colores_normalizados():
    """Convierte la paleta BGR (OpenCV) de config a RGB normalizado (0-1)
    para que matplotlib la interprete correctamente."""
    return [tuple(c / 255 for c in color[::-1]) for color in config.COLORES]


def plot_grafo_agregado(g, out_path=None):
    """Dibuja el grafo agregado de transiciones entre teclas, con el grosor
    de arista proporcional al peso (frecuencia de uso)."""
    out_path = out_path or os.path.join(OUTPUTS_DIR, "grafo_teclado.png")
    pos = {p: (i, 0) for i, p in enumerate(config.PALABRAS)}

    plt.figure(figsize=(11, 3))
    nx.draw_networkx_nodes(g, pos, node_color=_colores_normalizados(), node_size=1400)
    nx.draw_networkx_labels(g, pos, font_size=8)
    pesos = [g[u][v]["weight"] for u, v in g.edges()]
    nx.draw_networkx_edges(
        g, pos, connectionstyle="arc3,rad=0.3",
        width=[1 + w_ for w_ in pesos] if pesos else 1,
        arrowsize=15, edge_color="gray",
    )
    plt.title("Grafo de transiciones entre teclas (agregado)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path


def plot_evolucion(snapshots, out_path=None):
    """Dibuja una fila de instantáneas del grafo a medida que se agregan
    selecciones, tal como devuelve `graph_analysis.reconstruir_evolucion`."""
    out_path = out_path or os.path.join(OUTPUTS_DIR, "evolucion_grafo.png")
    if not snapshots:
        return None

    pos = {p: (i, 0) for i, p in enumerate(config.PALABRAS)}
    colores = _colores_normalizados()

    fig, axes = plt.subplots(1, len(snapshots), figsize=(5 * len(snapshots), 3))
    if len(snapshots) == 1:
        axes = [axes]

    for ax, (n_selecciones, gt) in zip(axes, snapshots):
        nx.draw_networkx_nodes(gt, pos, ax=ax, node_size=800, node_color=colores)
        nx.draw_networkx_labels(gt, pos, ax=ax, font_size=6)
        nx.draw_networkx_edges(gt, pos, ax=ax, connectionstyle="arc3,rad=0.3",
                                arrowsize=10, edge_color="gray")
        ax.set_title(f"Tras {n_selecciones} selecciones")
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path


def plot_centralidades(centralidades_df, out_path=None, metrica="pagerank"):
    """Gráfico de barras horizontal con una métrica de centralidad por tecla."""
    out_path = out_path or os.path.join(OUTPUTS_DIR, "centralidades.png")
    datos = centralidades_df.sort_values(metrica)

    plt.figure(figsize=(7, 4))
    plt.barh(datos.index, datos[metrica], color="#4285F4")
    plt.xlabel(metrica)
    plt.title(f"Centralidad de las teclas ({metrica})")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path
