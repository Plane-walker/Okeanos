# import unittest
# from dock.netopter import NetworkOptimizer
# from interface.dci.dci_pb2 import RequestCommunityInfo
#
#
# class TestNetworkOptimizer(unittest.TestCase):
#     def test_switch_community(self):
#         network_optimizer = NetworkOptimizer('0', '0')
#         response = network_optimizer.community_info(RequestCommunityInfo(info_level=0))
#         self.assertEqual(response.community_id, '0')
#         self.assertEqual(response.node_id, '0')
#
#
# if __name__ == '__main__':
#     unittest.main()
