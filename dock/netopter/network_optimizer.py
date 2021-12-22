__all__ = [
    'NetworkOptimizer'
]

from .node_classification import GraphSAGEModel
from .graph_data import GraphData
from interface.dci.dci_pb2 import ResponseSwitchCommunity


class NetworkOptimizer:
    def __init__(self, node_id, community_id):
        self.node_id = node_id
        self.community_id = community_id
        self.graph_data = GraphData()
        self.model = GraphSAGEModel()

    def create_community(self):
        pass

    def get_node_representation(self,
                                trained_model=False,
                                model_path='models/graph_sage.tf',
                                save_model=False,
                                save_path='models/graph_sage.tf'):
        if trained_model:
            self.model.load(model_path)
        else:
            self.model.train(self.graph_data)
            if save_model:
                self.model.save(save_path)
        return self.model.predict(self.graph_data)

    def switch_community(self, request):
        self.leave_community()
        self.join_community(request.target_community)
        return ResponseSwitchCommunity(code=200, info='ok')

    def leave_community(self):
        pass

    def join_community(self, target_community):
        self.community_id = target_community
        self.graph_data.get_data_from_neighbors()
        node_representation = self.get_node_representation()

    def community_info(self):
        pass

    def community_config(self):
        pass
