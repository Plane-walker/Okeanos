__all__ = [
    'NetworkOptimizer'
]

from log import log
from .node_classification import GraphSAGEModel
from .graph_data import GraphData
from interface.dci import dci_pb2


class NetworkOptimizer:
    def __init__(self, config_path):
        self.graph_data = GraphData(config_path)
        self.config_path = config_path
        self.model = GraphSAGEModel(config_path=config_path)

    def update_model(self):
        self.model.train(self.graph_data)
        self.model.save_model()

    def switch_island(self, request):
        self.graph_data.update_neighbors_data()
        new_chain_id = self.model.predict(self.graph_data)
        log.info(f'New chain id is {new_chain_id}')
        return dci_pb2.ResponseSwitchIsland(code=200, info='ok')
