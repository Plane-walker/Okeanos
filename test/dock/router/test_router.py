# import unittest
# import uuid
# from concurrent import futures
# import grpc
# from interface.dci import dci_pb2_grpc, dci_pb2
# from dock.router import Router
# from dock import DockServer
# from interface.common.id_pb2 import Chain
# from log import log
#
#
# class TestRouter(unittest.TestCase):
#
#     def setUp(self):
#         print('SetUp')
#         self.router = Router('dock/config/default_config.yaml')
#         self.test_num = 5
#         self.ids = []
#         for _ in range(self.test_num):
#             identifier = uuid.uuid4().hex
#             self.router.route[identifier] = Chain(identifier=identifier)
#             self.ids.append(identifier)
#         server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#         dock = DockServer(self.router, None, None)
#         dci_pb2_grpc.add_DockServicer_to_server(
#             dock, server
#         )
#         self.addr = 'localhost:1453'
#         server.add_insecure_port(self.addr)
#         server.start()
#
#     def test_next_node(self):
#         log.debug('')
#         for identifier in self.ids:
#             self.assertTrue(identifier in self.router.route)
#             self.assertEqual(
#                 identifier,
#                 self.router.next_node(
#                     Chain(identifier=identifier)
#                 ).identifier
#             )
#         for _ in range(self.test_num):
#             self.assertIsNone(self.router.next_node(
#                 Chain(identifier=uuid.uuid4().hex)))
#
#     def test_info(self):
#         log.debug('')
#         with grpc.insecure_channel(self.addr) as channel:
#             stub = dci_pb2_grpc.DockStub(channel)
#             res = stub.RouterInfo(dci_pb2.RequestRouterInfo(tx=1234))
#             self.assertIsInstance(res, dci_pb2.ResponseRouterInfo)
#             self.assertIs(res.code, 0)
#
#     def test_transmit(self):
#         log.debug('')
#         with grpc.insecure_channel(self.addr) as channel:
#             stub = dci_pb2_grpc.DockStub(channel)
#             res = stub.RouterTransmit(
#                 dci_pb2.RequestRouterTransmit(
#                     source=Chain(identifier='1234'),
#                     target=Chain(identifier='4321'),
#                     ttl=3,
#                     paths=[Chain(identifier='4321')]
#                 )
#             )
#             self.assertIsInstance(res, dci_pb2.ResponseRouterTransmit)
#             self.assertIs(res.code, 0)
#
#     def test_callback(self):
#         log.debug('')
#         with grpc.insecure_channel(self.addr) as channel:
#             stub = dci_pb2_grpc.DockStub(channel)
#             res = stub.RouterPathCallback(
#                 dci_pb2.RequestRouterPathCallback(
#                     source=Chain(identifier='4321'),
#                     target=Chain(identifier='1234'),
#                     paths=[Chain(identifier='1234')]
#                 )
#             )
#             self.assertIsInstance(res, dci_pb2.ResponseRouterPathCallback)
#             self.assertIs(res.code, 0)
#
#
# if __name__ == '__main__':
#     unittest.main()
