"""
Grafo de predicción / autocompletado.

Es, en esencia, un modelo de lenguaje bigrama sobre un vocabulario cerrado
de 10 palabras: se inicializa con un conjunto semilla de transiciones
típicas y se refuerza (+1 de peso) cada vez que el usuario confirma una
transición real, de modo que el teclado "aprende" con el uso.
"""
import networkx as nx

from . import config


def construir_grafo_prediccion():
    """Crea el grafo de predicción `G_pred`, con los 10 nodos del teclado
    y las transiciones semilla definidas en `config.SEMILLA_TRANSICIONES`."""
    g_pred = nx.DiGraph()
    g_pred.add_nodes_from(config.PALABRAS)
    for (u, v), peso in config.SEMILLA_TRANSICIONES.items():
        g_pred.add_edge(u, v, weight=peso)
    return g_pred


def sugerir_siguientes(g_pred, palabra, top_k=config.TOP_K_SUGERENCIAS):
    """Devuelve hasta `top_k` sucesores de `palabra` en `g_pred`, ordenados
    por peso descendente (las palabras más probables para continuar)."""
    if palabra not in g_pred:
        return []
    vecinos = [(v, g_pred[palabra][v]["weight"]) for v in g_pred.successors(palabra)]
    vecinos.sort(key=lambda t: t[1], reverse=True)
    return [v for v, _ in vecinos[:top_k]]


def reforzar_transicion(g_pred, u, v):
    """Incrementa en 1 el peso de la arista u->v (o la crea con peso 1)."""
    if g_pred.has_edge(u, v):
        g_pred[u][v]["weight"] += 1
    else:
        g_pred.add_edge(u, v, weight=1)
