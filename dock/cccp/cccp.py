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
        self.router = router

    def parse_tx_package(self, tx_passage):
        # Parse RequestTxPackage to get it's content.
        # Content can be used for the following functions.
        tx = tx_passage.tx
        target_id = tx_passage.target_id
        node_id = tx_passage.node_id
        flag = tx_passage.flag
        next_route_path = self.router.next_node(self.target_id)
        return tx, target_id, node_id, next_route_path

    def publish_tx(self, tx, target_id, flag, node_id, next_route_path):
        req = RequestPublishTX(
            tx=tx,
            target_id=target_id,
            node_id=node_id,
            flag=flag,
            route_path=next_route_path
        )
        # with grpc.insecure_channel('localhost:1453') as channel:
        #     log.info('successfully connect to ', channel)
        #     stub = LaneStub(channel)
        #     res = stub.PublishTX(req)
        #     # After obtaining return : res.TxPublishCode.Success.value
        #     log.info(res)
        lane = self.router[next_route_path]
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'method': 'broadcast_tx_sync',
            'params': {
                'tx': json.dumps(MessageToJson(req))
            }
        }
        log.info('Connect to ', f'http://localhost:{str(lane.port)}')
        response = requests.post(f'http://localhost:{str(lane.port)}', headers=headers, data=data).json()
        log.info(response)

    def deliver_tx_to_next_chain(self, request_tx: RequestTxPackage):
        if request_tx is not None:
            tx, target_id, node_id, next_route_path = self.parse_tx_package(request_tx)
            self.publish_tx(tx, target_id, node_id, next_route_path)
            return ResponseTxPackage(code=TxDeliverCode.Success.value)
        else:
            return ResponseTxPackage(code=TxDeliverCode.FAIL.value)

