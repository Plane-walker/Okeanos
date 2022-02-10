__all__ = [
    'CrossChainCommunicationProtocol'
]


from enum import Enum, unique
import requests
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
        lane_chain = self.chain_manager[self.router.next_jump(request.target)]
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'method': 'broadcast_tx_sync',
            'params': {
                'tx': request.tx
            }
        }
        log.info('Connect to ', f'http://localhost:{lane_chain.rpc_port}')
        response = requests.post(f'http://localhost:{lane_chain.rpc_port}', headers=headers, data=data).json()
        log.info(response)

    def deliver_tx(self, request: RequestDeliverTx):
        if request is not None:
            if request.target in self.chain_manager.chains.keys():
                chain = self.chain_manager.chains[request.target]
                headers = {
                    'Content-Type': 'application/json',
                }
                data = {
                    'method': 'broadcast_tx_sync',
                    'params': {
                        'tx': request.tx
                    }
                }
                log.info('Connect to ', f'http://localhost:{chain.port}')
                response = requests.post(f'http://localhost:{chain.port}', headers=headers, data=data).json()
                log.info(response)
            else:
                self.transfer_tx(request)
            return ResponseDeliverTx(code=TxDeliverCode.Success.value)
        else:
            return ResponseDeliverTx(code=TxDeliverCode.FAIL.value)

