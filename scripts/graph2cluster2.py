import sys
import networkx as nx
from modules import transform_edge_weights, scale_weights, get_node_std, get_data_maps_edges, get_excluded_nodes, get_nan_edges
from cluster_ import add_clusters, get_clusters
from correlation import cluster_correlation_search
from clustering_interface import louvain_clustering, chinese_whispers_clustering
import csv
import numpy as np
 
[_, input_file, threshold, modus, ambiguity, algorithm, degree, is_clean, annotators, output_file] = sys.argv

    
threshold=float(threshold)
graph = nx.read_gpickle(input_file)

    
with open(annotators, encoding='utf-8') as csvfile: 
    reader = csv.DictReader(csvfile, delimiter='\t',quoting=csv.QUOTE_NONE,strict=True)
    annotators = [row['annotator'] for row in reader]

if is_clean=='True':
    is_clean=True
if is_clean=='False':
    is_clean=False

try: # search previous clustering for initialization
    initial, _, _ = get_clusters(graph)
    noise, _, _ = get_clusters(graph, is_include_noise = True, is_include_main = False)
    print('Initializing with previous clustering.')
except KeyError: # no clusters found
    if is_clean: # make noise cluster
        initial = []
        mappings_edges = get_data_maps_edges(graph, annotators)
        node2judgments, node2weights = mappings_edges['node2judgments'], mappings_edges['node2weights']
        noise = [set(get_excluded_nodes(node2judgments, node2weights, share=0.5))]
    else:
        initial = []
        noise = [{}]

    
# Prepare graph for clustering    
G_clean = graph.copy()
G_clean.remove_nodes_from([node for cluster in noise for node in cluster]) # Remove noise nodes before ambiguity measures
nan_edges = get_nan_edges(G_clean)    
G_clean.remove_edges_from(nan_edges)
transformation = lambda x: x-threshold
G_clean = transform_edge_weights(G_clean, transformation = transformation) # shift edge weights

# Remove influence of ambiguous nodes and edges
if ambiguity == 'remove_nodes':    
    node2stds = get_node_std(G_clean, annotators)
    nodes_high_stds = [n for n in G_clean.nodes() if np.nanmean(node2stds[n])>0.3]
    noise.append(set(nodes_high_stds))
    G_clean.remove_nodes_from(nodes_high_stds)    
if ambiguity == 'scale_edges':        
    G_clean = scale_weights(G_clean, 'std', annotators)    
if ambiguity == 'None':
    pass

if modus=='test':
    max_attempts = 10
    max_iters = 10
    s = 2
if modus=='system':
    max_attempts = 1000
    max_iters = 5000 
    s = 10
if modus=='full':
    max_attempts = 2000
    max_iters = 50000
    s = 20

    
if algorithm=='correlation':
    clusters, cluster_stats = cluster_correlation_search(G_clean, s = s, max_attempts = max_attempts, max_iters = max_iters, initial = initial) # rather good performance: 2000, 50000
    cluster_stats = cluster_stats | {'algorithm':algorithm, 'threshold':threshold, 'ambiguity':ambiguity}
if algorithm=='chinese':
    clusters = chinese_whispers_clustering(G_clean, weighting = degree)
    cluster_stats = {}
    cluster_stats = cluster_stats | {'algorithm':algorithm, 'threshold':threshold, 'ambiguity':ambiguity, 'degree':degree}
if algorithm=='wsbm':
    clusters = wsbm_clustering(G_clean)
    cluster_stats = {}
    cluster_stats = cluster_stats | {'algorithm':algorithm, 'threshold':threshold, 'ambiguity':ambiguity}
if algorithm=='louvain':
    clusters = louvain_clustering(G_clean)
    cluster_stats = {}
    cluster_stats = cluster_stats | {'algorithm':algorithm, 'threshold':threshold, 'ambiguity':ambiguity}

# Store results
graph.graph['cluster_stats'] = cluster_stats
print('number of clusters: ', len(clusters))
node2cluster = {node:i for i, cluster in enumerate(clusters) for node in cluster} | {node:-1 for cluster in noise for node in cluster}
graph = add_clusters(graph, node2cluster)

nx.write_gpickle(graph, output_file)
