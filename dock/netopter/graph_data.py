__all__ = [
    'GraphData'
]

import json
import os
import grpc
import pandas as pd
import networkx as nx
import numpy as np
from sklearn.preprocessing import LabelBinarizer
from interface.dci import dci_pb2


class GraphData:
    def __init__(self):
        self._connection_weight = {}
        self._app_chain_id = {}

    def get_graph_data(self, request):
        response = dci_pb2.ResponseGetGraphData()
        for app_id, weight in self._connection_weight.items():
            response.app_id.append(app_id)
            response.weight.append(weight)
            response.chain_id.append(self._app_chain_id[app_id])
        return response

    def update_graph_data(self, request):
        self._app_chain_id[request.app_id] = request.chain_id
        self._connection_weight[request.app_id] = self._connection_weight.get(request.app_id, 0) + request.increase_weight
        return dci_pb2.ResponseUpdateGraphData(code=0, info='OK')

    # def get_data_from_neighbors(self):
    #     # channel = grpc.insecure_channel('localhost:1453')
    #     # client = bci_pb2_grpc.LaneStub(channel=channel)
    #     # response = client.GetNeighborInfo()
    #     headers = {
    #         'Content-Type': 'application/json',
    #     }
    #     data = {
    #         'method': 'broadcast_tx_sync',
    #         'params': {}
    #     }
    #     log.info('Connect to ', f'http://localhost:1453')
    #     response = requests.post(f'http://localhost:1453', headers=headers, data=data).json()
    #     log.info(response)
    #     self.adjacency_matrix = response.adjacency_matrix
    #     self.feature = response.feature
    #     self.id_map = response.id_amp
    #
    # def import_data_from_file(self, file_path):
    #     cites = pd.read_csv(os.path.join(file_path, 'cora.cites'), sep='\t', header=None).values
    #     content = pd.read_csv(os.path.join(file_path, 'cora.content'), sep='\t', header=None).values
    #     id_map = content[:, 0]
    #     feature = content[:, 1: -1]
    #     label = content[:, -1]
    #     label = LabelBinarizer().fit_transform(label)
    #     graph = nx.Graph()
    #     graph.add_edges_from(cites)
    #     adjacency_matrix = np.array(nx.convert_matrix.to_numpy_matrix(graph, nodelist=id_map))
    #     feature = np.array(feature, dtype=np.float32)
    #     self.adjacency_matrix = adjacency_matrix
    #     self.feature = feature
    #     self.label = label
    #     self.id_map = id_map
    #
    # def find_community_id(self, node_representation):
    #     return self.community_id_map[node_representation]
