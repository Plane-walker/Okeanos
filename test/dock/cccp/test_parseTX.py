import grpc
import unittest
from interface.dci import dci_pb2_grpc, dci_pb2
from interface.dci.dci_pb2 import Chain, Node


class TestCCCP(unittest.TestCase):
    def test_get_target_id(self):
        with grpc.insecure_channel("localhost:1453") as channel:
            stub = dci_pb2_grpc.DockStub(channel)
            res: dci_pb2.ResponseMessage = stub.PackageTx(
                dci_pb2.RequestTxPackage(
                    # tx=12121,
                    target_id=Chain(identifier=1234),
                    node_id=Node(identifier=2345)
                )
            )
            print(res.message)


if __name__ == '__main__':
    unittest.main()

