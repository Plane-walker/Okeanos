from dock.cccp import CrossChainCommunicationProtocol
import unittest


class TestCCCP(unittest.TestCase):
    def test_parse_tx_package(self):
        self.data = {'target_id': '1234', 'node_id': '2345'}
        CrossChainCommunicationProtocol.parse_tx_package(self.data)


if __name__ == '__main__':
    unittest.main()

