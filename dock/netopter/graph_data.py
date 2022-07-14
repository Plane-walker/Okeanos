__all__ = [
    'GraphData'
]

import os
import pandas as pd
import networkx as nx
import json
import numpy as np
from sklearn.preprocessing import LabelBinarizer


class GraphData:
    def __init__(self, config_path):
        self._config_path = config_path
        self._vertices = {}
        self._edges = {}
        self._labels = {}

    def import_data(self):
        id_map = np.array(list(self._vertices.keys()))
        features = np.array([list(map(int, list(''.join([bin(ord(c)).replace('0b', '') for c in self._vertices[vertex_id]]) + '0' * 100)[0: 100])) for vertex_id in id_map])
        adjacency_matrix = np.array([[self._edges.get((source_id, target_id), 0) for target_id in id_map] for source_id in id_map])
        labels = np.array([self._labels[vertex_id] for vertex_id in id_map])
        return id_map.reshape([id_map.shape[0], -1]), features.reshape([features.shape[0], -1]), adjacency_matrix, labels.reshape([labels.shape[0], -1])

    def import_data_from_str(self, graph_state):
        node_connections = json.loads(graph_state)
        for node_connection in node_connections:
            self._vertices[node_connection['source_node_id']] = node_connection['source_info']
            self._vertices[node_connection['target_node_id']] = node_connection['target_info']
            edge = (node_connection['source_node_id'], node_connection['target_node_id'])
            self._edges[edge] = self._edges.get(edge, 0) + len(node_connection['weight'])
            self._edges[(node_connection['target_node_id'], node_connection['source_node_id'])] = self._edges[edge]
            self._labels[node_connection['source_node_id']] = node_connection['source_chain_id']
            self._labels[node_connection['target_node_id']] = node_connection['target_chain_id']

    @staticmethod
    def import_data_from_file(file_path):
        cites = pd.read_csv(os.path.join(file_path, 'cora.cites'), sep='\t', header=None).values
        content = pd.read_csv(os.path.join(file_path, 'cora.content'), sep='\t', header=None).values
        id_map = content[:, 0]
        feature = content[:, 1: -1]
        label = content[:, -1]
        labels = LabelBinarizer().fit_transform(label)
        graph = nx.Graph()
        graph.add_edges_from(cites)
        adjacency_matrix = np.array(nx.convert_matrix.to_numpy_matrix(graph, nodelist=id_map))
        features = np.array(feature, dtype=np.float32)
        return id_map, features, adjacency_matrix, labels
