__all__ = [
    'GraphData'
]

import os
import pandas as pd
import networkx as nx
import numpy as np
from sklearn.preprocessing import LabelBinarizer
from interface.dci import dci_pb2


class GraphData:
    def __init__(self):
        self._vertices = {}
        self._edges = {}
        self._labels = {}

    def get_graph_data(self, request):
        response = dci_pb2.ResponseGetGraphData()
        for (source_id, target_id), weight in self._edges.items():
            if source_id in request.app_id:
                node_connection = dci_pb2.NodeConnection(source_app_id=source_id,
                                                         source_app_info=self._vertices[source_id],
                                                         source_app_chain_id=self._labels[source_id],
                                                         target_app_id=target_id,
                                                         target_app_info=self._vertices[target_id],
                                                         target_app_chain_id=self._labels[target_id],
                                                         weight=weight)
                response.node_connections.append(node_connection)
        return response

    def update_graph_data(self, request):
        for node_connection in request.node_connections:
            self._vertices[node_connection.source_app_id] = node_connection.source_app_info
            self._vertices[node_connection.target_app_id] = node_connection.target_app_info
            edge = (node_connection.source_app_id, node_connection.target_app_id)
            self._edges[edge] = self._edges.get(edge, 0) + node_connection.weight
            self._edges[(node_connection.target_app_id, node_connection.source_app_id)] = self._edges[edge]
            self._labels[node_connection.source_app_id] = node_connection.source_app_chain_id
            self._labels[node_connection.target_app_id] = node_connection.target_app_chain_id
        return dci_pb2.ResponseUpdateGraphData(code=0, info='OK')

    def get_all_data(self):
        id_map = np.array(self._vertices.keys())
        features = np.array([self._vertices[vertex_id] for vertex_id in id_map])
        adjacency_matrix = np.array([[self._edges.get((source_id, target_id), 0) for target_id in id_map] for source_id in id_map])
        labels = np.array([self._labels[vertex_id] for vertex_id in id_map])
        return id_map, features, adjacency_matrix, labels

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
