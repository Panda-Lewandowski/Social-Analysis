import networkx as nx
import names 
import requests
import random

def read_graph_from_edgelist(file, directed):
    if file.readline() == "directed\n":
        directed = True

    if directed: 
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    nodes = set()
    edges = []
    for line in file:
        if isinstance(line, bytes):
            line = line.decode('utf-8')
        e = line[:-1].split(" ")
        G.add_edge(*e)
        if directed:
            edges.append({'from': e[0], 'to': e[1], 'arrows': 'to'})
        else:
            edges.append({'from': e[0], 'to': e[1]})
        nodes.add(e[0])
        nodes.add(e[1])
    new_nodes = []
    for x in nodes:
        name = names.get_full_name()
        new_nodes.append({'id': x, 'label': name, 'title': '<h4 class="fs-6"><b>' + name + 
                                f", {random.randint(20, 36)} [id={x}]</b></h4><br>"})
    return G, new_nodes, edges, directed