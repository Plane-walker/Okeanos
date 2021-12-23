import unittest
import uuid
from concurrent import futures
import grpc
from interface.dci import dci_pb2_grpc, dci_pb2
from dock.router import Router
from dock import DockServer
from interface.dci.dci_pb2 import (
    Chain,
)


class TestRouter(unittest.TestCase):
    
    # def test_next_node(self):
    #     router = Router()
    #     ids = []
    #     TEST_NUM = 5
    #     for _ in range(TEST_NUM):
    #         identifier = uuid.uuid4().fields[0]
    #         router.paths[identifier] = Chain(identifier=identifier)
    #         ids.append(identifier)
    #     for id in ids:
    #         self.assertTrue(id in router.paths)
    #         self.assertEqual(id, router.next_node(Chain(identifier=id)).identifier)
    #     for _ in range(TEST_NUM):
    #         self.assertIsNone(router.next_node(Chain(identifier=uuid.uuid4().fields[0])))

    def test_client(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(DockServer(Router()), server)
        host = 'localhost'
        port = '1453'
        server.add_insecure_port(f'{host}:{port}')
        server.start()
        channel = grpc.insecure_channel('localhost:1453')
        stub = dci_pb2_grpc.DockStub(channel)
        res = stub.RouterInfo(dci_pb2.RequestRouterInfo(tx=1234))
        print(type(res))
        print(res)
        print("Client RouterInfo Test Finish...\n")

        res = stub.RouterTransmit(dci_pb2.RequestRouterTransmit(source=Chain(identifier=1234), target=Chain(identifier=4321),ttl=3,paths=[Chain(identifier=4321)]))
        print(type(res))
        print(res.code)
        print("Client RouterTransmit Test Finish...")


if __name__ == '__main__':
    unittest.main()
