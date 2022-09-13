import networkx as nx
import itertools
import os 
import powerlaw

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage

from networkx.algorithms import community
from networkx.algorithms.clique import graph_number_of_cliques
from cdlib import algorithms
from graph.core.algorithms import find_bridges

from .utils import read_graph_from_edgelist

cent_funcs = {"degree_centrality": nx.degree_centrality, 
            "eigenvector_centrality": nx.eigenvector_centrality,
            "closeness_centrality":  nx.closeness_centrality,
            "betweenness_centrality": nx.betweenness_centrality,
            "harmonic_centrality": nx.harmonic_centrality}

both_comm_func = {
    "leiden": algorithms.leiden,
    "walktrap": algorithms.walktrap,
    "infomap": algorithms.infomap,
    "eigenvector": algorithms.eigenvector,
    "belief": algorithms.belief,
    "chinesewhispers": algorithms.chinesewhispers,
    "markov_clustering": algorithms.markov_clustering,
    "rber_pots": algorithms.rber_pots,
    "rb_pots": algorithms.rb_pots,
    "significance_communities": algorithms.significance_communities,
    "spinglass": algorithms.spinglass,
    "surprise_communities": algorithms.surprise_communities,
    "agdl": [algorithms.agdl, {"number_communities": 3, "kc":4}],
    "girvan_newman": [algorithms.girvan_newman, {"level": 3}],
    # overlapping
    "aslpaw": algorithms.aslpaw,
    "demon": [algorithms.demon, {"epsilon": 0.25}], 
    "ego_networks": algorithms.ego_networks,
    "lfm": [algorithms.lfm, {"alpha":0.8}],
    "node_perception": [algorithms.node_perception, {"threshold": 0.25, "overlap_threshold": 0.25}],
    "slpa": algorithms.slpa,
}

non_dir_comm_func = {
    "greedy_modularity": algorithms.greedy_modularity,
    "louvain": algorithms.louvain,
    "async_fluid": [algorithms.async_fluid, {"k": 3}],
    "der": algorithms.der,
    "edmot": algorithms.edmot,
    "em": [algorithms.em, {"k": 3}],
    "ga": algorithms.ga,
    "label_propagation": algorithms.label_propagation,
    # overlapping
    "big_clam": algorithms.big_clam,
    "conga": [algorithms.conga, {"number_communities": 3}],
    "congo": [algorithms.congo, {"number_communities": 3}],
    "danmf": algorithms.danmf,
    "egonet_splitter": algorithms.egonet_splitter,
    "kclique": [algorithms.kclique, {"k": 3}],
    "lais2": algorithms.lais2,
    "multicom": algorithms.multicom,
    "nnsed": algorithms.nnsed,
    "percomvc": algorithms.percomvc
}


def index(request):
    centrality_type = 'degree_centrality'
    community_type = 'girvan_newman'
    short_path = False
    directed = False
    connected = False
    strongly_connected = False

    if request.method == 'POST' and request.FILES:
        file = request.FILES['filegraph']
        directed = request.POST.get('directed', False)
        with open(os.path.join(settings.MEDIA_ROOT, 'current.txt'), 'wb+') as destination:
            if directed:
                destination.write("directed\n".encode('utf-8'))
            for chunk in file.chunks():
                destination.write(chunk)
    elif request.method == 'POST' and request.POST.get('centralities', False):
        centrality_type = request.POST['centralities'] 
        community_type = request.POST['communities']
        file  = open(os.path.join(settings.MEDIA_ROOT, 'current.txt'))
    elif request.method == 'POST':
        from_node = request.POST.get('from-node').replace(" ", "")
        to_node = request.POST.get('to-node').replace(" ", "")
        file  = open(os.path.join(settings.MEDIA_ROOT, 'current.txt'))
        short_path = True
    else:
        file  = open(os.path.join(settings.MEDIA_ROOT, 'current.txt')) 
            
    G, nodes, edges, directed = read_graph_from_edgelist(file, directed)

    if short_path:
        try:
            path = nx.shortest_path(G, source=from_node, target=to_node)
        except nx.NetworkXNoPath:
            path = "false"

    number_of_edges = G.number_of_edges()
    number_of_nodes = G.number_of_nodes()
    number_of_selfloops = nx.number_of_selfloops(G)

    if not directed:
        connected = nx.is_connected(G)
    elif nx.is_strongly_connected(G) or nx.is_weakly_connected(G):
        connected = True
        
    if directed:
        if nx.is_strongly_connected(G):
            strongly_connected = True
            G_strong = G.subgraph(max(nx.strongly_connected_components(G), key=len))
            nodes_strong = G_strong.number_of_nodes()
            edges_strong = G_strong.number_of_edges()
            av_path_strong = round(nx.average_shortest_path_length(G_strong), 4)
            rec_strong = nx.overall_reciprocity(G_strong)
        G_weak = G.subgraph(max(nx.weakly_connected_components(G), key=len))
        nodes_weak = G_weak.number_of_nodes()
        edges_weak = G_weak.number_of_edges()
        av_path_weak = round(nx.average_shortest_path_length(G_weak), 4)
        rec_weak = nx.overall_reciprocity(G_weak)
    
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    dmax = max(degree_sequence)
    av_degree = round(sum(degree_sequence) / len(degree_sequence))
    exp = round(powerlaw.Fit(degree_sequence, verbose=False).alpha, 3)
    if connected:
        diameter = nx.diameter(G.to_undirected())
        av_path = round(nx.average_shortest_path_length(G.to_undirected()), 4) 
        center = nx.center(G.to_undirected()) 
        periphery = nx.periphery(G.to_undirected()) 

    transitivity = round(nx.transitivity(G), 4)
    clustering = round(nx.average_clustering(G), 4)
    reciprocity = round(nx.overall_reciprocity(G), 4)
    connectivity = round(nx.node_connectivity(G), 4)
    assortativity = round(nx.degree_assortativity_coefficient(G), 4) 

    constraint = nx.constraint(G)
    for n in nodes:
        n['title'] = n['title'] + f"Constraint: {round(constraint[n['id']], 5)}<br>" 
        if constraint[n['id']] <= 0.2:
            n['shape'] = "hexagon"

   

    c = cent_funcs[centrality_type](G)
    for n in nodes:
        n['value'] = round(c[n['id']], 2)
        n['title'] = n['title'] + f"{centrality_type.replace('_', ' ')}: {round(c[n['id']], 5)}<br>"

    comm_func = both_comm_func   

    if not directed:
        number_of_triangles = round(sum(nx.triangles(G).values()) / 3)
        number_of_clique = graph_number_of_cliques(G)
        comm_func = non_dir_comm_func | both_comm_func
        bridges = list(nx.bridges(G))
        for e in edges:
            if ((e['to'], e['from']) in bridges) or \
                                            ((e['from'], e['to']) in bridges):
                
                e.update({'dashes': 'true'})


    comm = comm_func[community_type]
    if isinstance(comm, list):
        params = comm[1]
        comm_res = comm[0](G, **params).communities 
    else:
        comm_res = comm(G).communities
    
    for n in nodes:
        local_comm = []
        for i in range(len(comm_res)):
            if n['id'] in comm_res[i]:
                local_comm.append(i)

        if len(local_comm) == 1: 
            n['group'] = local_comm[0]
        n['title'] = n['title'] + f"Communities: {local_comm}<br>"     

    return render(request, 'index.html', locals())

