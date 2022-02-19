__all__ = [
    'CrossChainCommunicationProtocol'
]


from enum import Enum, unique
import requests
import json
from interface.dci.dci_pb2 import RequestDeliverTx, ResponseDeliverTx
from log import log


@unique
class TxDeliverCode(Enum):
    Success = 0
    FAIL = 1


class CrossChainCommunicationProtocol:

    def __init__(self, router, chain_manager):
        self.lane = None
        self.router = router
        self.chain_manager = chain_manager

    def transfer_tx(self, request):
        lane = self.router.next_jump(request.target)
        tx_json = json.loads(request.tx.decode('utf-8'))
        params = (
            ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
        )
        log.info(f'Transfer cross-chain-tx to lane: {lane.chain_name}')
        response = requests.get(f'http://localhost:{lane.rpc_port}/broadcast_tx_commit', params=params)
        log.debug(f"{lane.chain_name} return: {response.text}")

    def deliver_tx(self, request: RequestDeliverTx):
        yield ResponseDeliverTx(code=TxDeliverCode.Success.value)
        island = self.chain_manager.get_island(request.target.identifier)
        if island is not None:
            tx_json = json.loads(request.tx.decode('utf-8'))
            tx_json.pop('target')
            params = (
                ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
            )
            log.info(f'Deliver cross-chain-tx to island: {island.chain_name}')
            response = requests.get(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params=params)
            log.debug(f"{island.chain_name} return: {response.text}")
        else:
            self.transfer_tx(request)

