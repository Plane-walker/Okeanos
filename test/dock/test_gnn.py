import unittest
from dock.interface.dci_pb2 import RouterChain


class TestNodeClassification(unittest.TestCase):
    def test_switch_community(self):
        re = RouterChain(identifier=1)
        self.assertEqual(re.identifier, 1)


if __name__ == '__main__':
    unittest.main()
