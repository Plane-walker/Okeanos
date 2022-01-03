from dock.cccp import CrossChainCommunicationProtocol
import unittest


class TestCCCP(unittest.TestCase):
    def test_get_target_id(self):
        self.data = {'target_id': '1234', 'node_id': '2345'}
        CrossChainCommunicationProtocol.get_target_id(self.data)


if __name__ == '__main__':
    unittest.main()

