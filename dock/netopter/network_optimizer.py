__all__ = [
    'NetworkOptimizer'
]

from .node_classification import GraphSAGEModel
from .graph_data import GraphData


class NetworkOptimizer:
    def __init__(self, node_id):
        self.node_id = node_id
        self.graph_data = GraphData()
        self.model = GraphSAGEModel()
