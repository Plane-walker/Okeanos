import unittest
from dock.netopter.node_classification import GraphSAGEModel
from dock.netopter.graph_data import GraphData


class TestNodeClassification(unittest.TestCase):
    def test_switch_community(self):
        data = GraphData()
        data.import_data_from_file('cora')
        graph_sage = GraphSAGEModel()
        graph_sage.train(data)


if __name__ == '__main__':
    unittest.main()
