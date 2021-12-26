import unittest
import uuid
from concurrent import futures
import grpc
from interface.dci import dci_pb2_grpc, dci_pb2
from dock.router import Router
from dock import DockServer
from interface.dci.dci_pb2 import Chain


class TestRouter(unittest.TestCase):

    def setUp(self):
        self.router = Router()
        self.test_num = 5
        self.ids = []
        for _ in range(self.test_num):
            identifier = uuid.uuid4().fields[0]
            self.router.route[identifier] = Chain(identifier=identifier)
            self.ids.append(identifier)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(DockServer(Router()), server)
        self.addr = 'localhost:1453'
        server.add_insecure_port(self.addr)
        server.start()

    def test_next_node(self):
        for identifier in self.ids:
            self.assertTrue(identifier in self.router.route)
            self.assertEqual(
                identifier,
                self.router.next_node(
                    Chain(identifier=identifier)
                ).identifier
            )
        for _ in range(self.test_num):
            self.assertIsNone(self.router.next_node(
                Chain(identifier=uuid.uuid4().fields[0])))

    def test_info(self):
        with grpc.insecure_channel(self.addr) as channel:
            stub = dci_pb2_grpc.DockStub(channel)
            res = stub.RouterInfo(dci_pb2.RequestRouterInfo(tx=1234))
            self.assertIsInstance(res, dci_pb2.ResponseRouterInfo)

    def test_transmit(self):
        with grpc.insecure_channel(self.addr) as channel:
            stub = dci_pb2_grpc.DockStub(channel)
            res = stub.RouterTransmit(
                dci_pb2.RequestRouterTransmit(
                    source=Chain(identifier=1234),
                    target=Chain(identifier=4321),
                    ttl=3,
                    paths=[Chain(identifier=4321)]
                )
            )
            self.assertIsInstance(res, dci_pb2.ResponseRouterTransmit)

    def test_callback(self):
        with grpc.insecure_channel(self.addr) as channel:
            stub = dci_pb2_grpc.DockStub(channel)
            res = stub.RouterPathCallback(
                dci_pb2.RequestRouterPathCallback(
                    source=Chain(identifier=4321),
                    target=Chain(identifier=1234),
                    paths=[Chain(identifier=1234)]
                )
            )
            self.assertIsInstance(res, dci_pb2.ResponseRouterPathCallback)


if __name__ == '__main__':
    unittest.main()
