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
        lane_chain = self.chain_manager.chains[self.router.next_jump(request.target)]
        tx_json = json.loads(request.tx.decode('utf-8'))
        params = (
            ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
        )
        log.info('0x' + json.dumps(tx_json).encode('utf-8').hex())
        log.info(f'Connect to http://localhost:{lane_chain.rpc_port}')
        response = requests.get(f'http://localhost:{lane_chain.rpc_port}/broadcast_tx_commit', params=params)
        log.info(response)

    def deliver_tx(self, request: RequestDeliverTx):
        yield ResponseDeliverTx(code=TxDeliverCode.Success.value)
        if request.target.identifier in self.chain_manager.chains.keys():
            chain = self.chain_manager.chains[request.target.identifier]
            tx_json = json.loads(request.tx.decode('utf-8'))
            tx_json.pop('target')
            params = (
                ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
            )
            log.info('0x' + json.dumps(tx_json).encode('utf-8').hex())
            log.info(f'Connect to http://localhost:{chain.rpc_port}')
            response = requests.get(f'http://localhost:{chain.rpc_port}/broadcast_tx_commit', params=params)
            log.info(response.text)
        else:
            self.transfer_tx(request)

