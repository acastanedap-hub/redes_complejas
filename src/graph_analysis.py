"""
Análisis topológico del grafo de interacción: agregación de sesiones,
métricas estructurales, centralidad, resiliencia, comunidades y un
proceso de difusión (cascada independiente).
"""
import random

import networkx as nx
import pandas as pd

from . import config


def unir_grafos(lista_grafos):
    """Une una lista de grafos de sesión en un único grafo agregado,
    sumando los pesos de las aristas repetidas."""
    g = nx.DiGraph()
    g.add_nodes_from(config.PALABRAS)
    for sub_g in lista_grafos:
        for u, v, d in sub_g.edges(data=True):
            if g.has_edge(u, v):
                g[u][v]["weight"] += d["weight"]
            else:
                g.add_edge(u, v, weight=d["weight"])
    return g


def calcular_metricas(g):
    """Densidad, grado medio y (sobre la versión no dirigida) diámetro y
    coeficiente de agrupamiento del grafo agregado."""
    gu = g.to_undirected()
    tiene_aristas = g.number_of_edges() > 0
    metricas = {
        "n_nodos": g.number_of_nodes(),
        "n_aristas": g.number_of_edges(),
        "densidad": round(nx.density(g), 3),
        "grado_medio": round(sum(dict(g.degree()).values()) / g.number_of_nodes(), 2),
        "componentes_conexas (no dirigido)": nx.number_connected_components(gu),
        "diametro_componente_mayor": (
            nx.diameter(gu.subgraph(max(nx.connected_components(gu), key=len)))
            if tiene_aristas else None
        ),
        "coef_agrupamiento_medio": round(nx.average_clustering(gu), 3) if tiene_aristas else 0,
    }
    return pd.DataFrame([metricas])


def calcular_centralidades(g):
    """Grado, intermediación, cercanía y PageRank para cada tecla,
    ordenadas por PageRank descendente."""
    tiene_aristas = g.number_of_edges() > 0
    df = pd.DataFrame({
        "grado": nx.degree_centrality(g),
        "intermediacion": nx.betweenness_centrality(g, weight="weight"),
        "cercania": nx.closeness_centrality(g),
        "pagerank": nx.pagerank(g, weight="weight") if tiene_aristas else {p: 0 for p in config.PALABRAS},
    }).round(3).sort_values("pagerank", ascending=False)
    return df


def analizar_resiliencia(g, centralidades):
    """Elimina la tecla de mayor PageRank y mide el impacto en la
    conectividad (tamaño de la componente mayor y n° de componentes)."""
    if g.number_of_edges() == 0:
        return None

    nodo_critico = centralidades["pagerank"].idxmax()
    gu_orig = g.to_undirected()
    tam_cc_orig = len(max(nx.connected_components(gu_orig), key=len))

    gu_sin_nodo = gu_orig.copy()
    gu_sin_nodo.remove_node(nodo_critico)
    if gu_sin_nodo.number_of_nodes() > 0 and gu_sin_nodo.number_of_edges() > 0:
        tam_cc_post = len(max(nx.connected_components(gu_sin_nodo), key=len))
    else:
        tam_cc_post = 1 if gu_sin_nodo.number_of_nodes() else 0

    return {
        "nodo_removido": nodo_critico,
        "tam_cc_antes": tam_cc_orig,
        "tam_cc_despues": tam_cc_post,
        "n_componentes_antes": nx.number_connected_components(gu_orig),
        "n_componentes_despues": nx.number_connected_components(gu_sin_nodo),
    }


def detectar_comunidades(g):
    """Comunidades (modularidad voraz) sobre la versión no dirigida del grafo."""
    if g.number_of_edges() == 0:
        return None
    gu = g.to_undirected()
    comunidades = list(nx.algorithms.community.greedy_modularity_communities(gu))
    modularidad = nx.algorithms.community.modularity(gu, comunidades)
    return {
        "comunidades": [sorted(c) for c in comunidades],
        "modularidad": round(modularidad, 3),
    }


def cascada_independiente(g, semilla, n_pasos=5, semilla_random=42):
    """Simula un modelo de cascada independiente: cada arista activa al
    nodo destino con probabilidad proporcional a su peso normalizado."""
    rng = random.Random(semilla_random)
    activos = {semilla}
    frontera = {semilla}
    historial = [set(activos)]
    max_w = max([d["weight"] for _, _, d in g.edges(data=True)], default=1)

    for _ in range(n_pasos):
        nueva_frontera = set()
        for nodo in frontera:
            for vecino in g.successors(nodo):
                if vecino not in activos:
                    prob = g[nodo][vecino]["weight"] / max_w
                    if rng.random() < prob:
                        nueva_frontera.add(vecino)
        activos |= nueva_frontera
        historial.append(set(activos))
        if not nueva_frontera:
            break
        frontera = nueva_frontera
    return historial


def reconstruir_evolucion(log_selecciones, n_cortes=4):
    """A partir del log de selecciones (en orden temporal real), reconstruye
    instantáneas del grafo en distintos puntos de avance, para visualizar
    cómo crece la red de interacción."""
    if not log_selecciones:
        return []

    pasos = sorted(log_selecciones, key=lambda p: p["frame"])
    indices = sorted(set(
        min(i, len(pasos) - 1)
        for i in [len(pasos) * k // n_cortes for k in range(1, n_cortes + 1)]
        if i >= 0
    ))

    snapshots = []
    for corte in indices:
        gt = nx.DiGraph()
        gt.add_nodes_from(config.PALABRAS)
        prev = None
        for p in pasos[:corte + 1]:
            if prev is not None and prev != p["palabra"]:
                if gt.has_edge(prev, p["palabra"]):
                    gt[prev][p["palabra"]]["weight"] += 1
                else:
                    gt.add_edge(prev, p["palabra"], weight=1)
            prev = p["palabra"]
        snapshots.append((corte + 1, gt))
    return snapshots
