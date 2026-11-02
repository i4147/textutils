from matplotlib import pyplot as plt
import networkx as nx


def word_frequency_plot(fdist):
    fdist.plot(25, cumulative=False)
    plt.show()


def lexical_graph(graph, size=(30, 24), dpi=80, **kwargs):
    if type(lexical_graph) != "dict":
        msg = "This method demands a adjacency list graph format"
        raise TypeError(msg)
    plt.figure(figsize=size, dpi=dpi)
    edges = []
    for i in graph:
        for v in graph[i]:
            edges.append([i, v])
    G = nx.Graph()
    G.add_edges_from(edges)
    nx.draw_networkx(G, kwads=kwargs)
    plt.show()


def dependency_trees(graph):
    pass
