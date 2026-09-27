"""
Pruebas rápidas de humo (smoke tests) para el módulo de análisis de
grafos y la simulación de datos. Ejecutar con:

    python -m pytest tests/ -v

o simplemente:

    python tests/test_graph_analysis.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import data_simulation, graph_analysis, prediction_graph, config


def test_construir_grafo_prediccion():
    g_pred = prediction_graph.construir_grafo_prediccion()
    assert set(g_pred.nodes) == set(config.PALABRAS)
    sugerencias = prediction_graph.sugerir_siguientes(g_pred, "TENGO")
    assert sugerencias[:2] == ["SED", "HAMBRE"] or set(sugerencias) == {"SED", "HAMBRE"}


def test_simular_sesiones_reproducible():
    r1 = data_simulation.simular_sesiones(n_mensajes=5, semilla_aleatoria=1)
    r2 = data_simulation.simular_sesiones(n_mensajes=5, semilla_aleatoria=1)
    assert r1["mensajes"] == r2["mensajes"]
    assert len(r1["mensajes"]) == 5


def test_unir_grafos_y_metricas():
    resultado = data_simulation.simular_sesiones(n_mensajes=6, semilla_aleatoria=3)
    g = graph_analysis.unir_grafos(resultado["grafos_sesion"])
    assert g.number_of_nodes() == len(config.PALABRAS)
    df_metricas = graph_analysis.calcular_metricas(g)
    assert "densidad" in df_metricas.columns


def test_centralidades_y_resiliencia():
    resultado = data_simulation.simular_sesiones(n_mensajes=8, semilla_aleatoria=5)
    g = graph_analysis.unir_grafos(resultado["grafos_sesion"])
    cent = graph_analysis.calcular_centralidades(g)
    assert set(cent.index) == set(config.PALABRAS)
    resiliencia = graph_analysis.analizar_resiliencia(g, cent)
    assert resiliencia is not None
    assert "nodo_removido" in resiliencia


def test_cascada_independiente():
    resultado = data_simulation.simular_sesiones(n_mensajes=6, semilla_aleatoria=9)
    g = graph_analysis.unir_grafos(resultado["grafos_sesion"])
    historial = graph_analysis.cascada_independiente(g, config.PALABRAS[0])
    assert isinstance(historial, list)
    assert config.PALABRAS[0] in historial[0]


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"\n{len(tests)} pruebas pasaron correctamente.")
