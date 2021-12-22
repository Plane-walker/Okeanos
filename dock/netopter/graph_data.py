__all__ = [
    'GraphData'
]

import os
import grpc
import pandas as pd
import networkx as nx
import numpy as np
from sklearn.preprocessing import LabelBinarizer
from interface.bci import bci_pb2, bci_pb2_grpc


class GraphData:
    def __init__(self, adjacency_matrix=None, feature=None, label=None, id_map=None):
        self.adjacency_matrix = adjacency_matrix
        self.feature = feature
        self.label = label
        self.id_map = id_map

    def get_data_from_neighbors(self):
        channel = grpc.insecure_channel('localhost:1453')
        client = bci_pb2_grpc.LaneStub(channel=channel)
        response = client.GetNeighborInfo()
        self.adjacency_matrix = response.adjacency_matrix
        self.feature = response.feature
        self.id_map = response.id_amp

    def import_data_from_file(self, file_path):
        cites = pd.read_csv(os.path.join(file_path, 'cora.cites'), sep='\t', header=None).values
        content = pd.read_csv(os.path.join(file_path, 'cora.content'), sep='\t', header=None).values
        id_map = content[:, 0]
        feature = content[:, 1: -1]
        label = content[:, -1]
        label = LabelBinarizer().fit_transform(label)
        graph = nx.Graph()
        graph.add_edges_from(cites)
        adjacency_matrix = np.array(nx.convert_matrix.to_numpy_matrix(graph, nodelist=id_map))
        feature = np.array(feature, dtype=np.float32)
        self.adjacency_matrix = adjacency_matrix
        self.feature = feature
        self.label = label
        self.id_map = id_map
