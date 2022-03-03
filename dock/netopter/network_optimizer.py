__all__ = [
    'NetworkOptimizer'
]

from log import log
from .node_classification import GraphSAGEModel
from .graph_data import GraphData
from interface.dci import dci_pb2


class NetworkOptimizer:
    def __init__(self, node_id, community_id, config_path):
        self.node_id = node_id
        self.community_id = community_id
        self.graph_data = GraphData()
        self.config_path = config_path
        self.model = GraphSAGEModel(config_path=config_path)

    def get_new_chain_id(self, trained_model=False, save_model=False):
        if trained_model:
            self.model.load()
        else:
            self.model.train(self.graph_data)
            if save_model:
                self.model.save()
        return self.model.predict(self.graph_data)

    def switch_island(self, request):
        new_chain_id = self.get_new_chain_id()
        log.info(f'New chain id is {new_chain_id}')
        return dci_pb2.ResponseSwitchIsland(code=200, info='ok')
