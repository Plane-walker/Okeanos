__all__ = [
    'CrossChainCommunicationProtocol'
]

import json

# import grpc
from enum import Enum, unique

from google.protobuf.json_format import MessageToJson
import requests

from interface.bci.bci_pb2 import (
    RequestPublishTX,
    ResponsePublishTX,
)
# from interface.bci import bci_pb2, bci_pb2_grpc
# from interface.bci.bci_pb2_grpc import LaneStub
from interface.dci.dci_pb2 import (
    RequestTxPackage,
    ResponseTxPackage,
)
from interface.common.id_pb2 import Chain
from log import log


@unique
class TxDeliverCode(Enum):
    Success = 0
    FAIL = 1


class CrossChainCommunicationProtocol:

    def __init__(self, router):
        self.lane = None
        self.router = router

    def parse_tx_package(self, tx_passage):
        # Parse RequestTxPackage to get it's content.
        # Content can be used for the following functions.
        tx = tx_passage.tx
        target = tx_passage.target
        source = tx_passage.source
        flag = tx_passage.flag
        self.lane = self.router.next_node(target)
        return tx, target, source, self.lane

    def publish_tx(self, tx, target, source, flag):
        req = RequestPublishTX(
            tx=tx,
            target=target,
            source=source,
            flag=flag
        )
        # with grpc.insecure_channel('localhost:1453') as channel:
        #     log.info('successfully connect to ', channel)
        #     stub = LaneStub(channel)
        #     res = stub.PublishTX(req)
        #     # After obtaining return : res.TxPublishCode.Success.value
        #     log.info(res)
        # lane = self.router[next_route_path]
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'method': 'broadcast_tx_sync',
            'params': {
                'tx': json.dumps(MessageToJson(req))
            }
        }
        log.info('Connect to ', f'http://localhost:{str(self.lane.port)}')
        response = requests.post(f'http://localhost:{str(self.lane.port)}', headers=headers, data=data).json()
        log.info(response)

    def deliver_tx_to_next_chain(self, request_tx: RequestTxPackage):
        if request_tx is not None:
            tx, target, source, flag = self.parse_tx_package(request_tx)
            if self.lane.identifier == target.identifier:
                # There should be a function to connect to DAPP.
                log.info("Target chain reached.")
            else:
                self.publish_tx(tx, target, source, flag)
                return ResponseTxPackage(code=TxDeliverCode.Success.value)
        else:
            return ResponseTxPackage(code=TxDeliverCode.FAIL.value)

