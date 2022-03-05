__all__ = [
    'CrossChainCommunicationProtocol'
]


from enum import Enum, unique
import requests
from interface.dci.dci_pb2 import RequestDeliverTx, ResponseDeliverTx
from log import log
from dock.router import Router
from .message import Message


@unique
class TxDeliverCode(Enum):
    Success = 0
    FAIL = 1


class CrossChainCommunicationProtocol:

    def __init__(self, config_path, chain_manager):
        self.lane = None
        self.router = Router(config_path, chain_manager)
        self.chain_manager = chain_manager

    def send(self, chain, msg):
        params = (
            ('tx', msg.get_hex()),
        )
        log.info(
            f'Send to {chain.chain_type}: '
            f'{chain.chain_name}({chain.chain_id}) with {msg.get_json()}'
        )
        response = requests.get(
            f'http://localhost:'
            f'{chain.rpc_port}/broadcast_tx_commit',
            params=params
        )
        log.info(f'{chain.chain_name} return: {response}')

    def deliver_tx(self, request: RequestDeliverTx):
        yield ResponseDeliverTx(code=TxDeliverCode.Success.value)
        try:
            log.debug('package msg . . .')
            msg = Message.from_req(request)
            if msg is None:
                raise ValueError('msg is None')
            if msg.get_type() not in Message.types:
                raise ValueError('msg type is not one of %s' % Message.types)
        except Exception as exception:
            log.error(repr(exception))
        else:
            log.debug(f'Recieve msg: {msg.get_json()}')
            if msg.get_type() == 'route':
                self.router.receiver(request.tx)
            elif msg.get_type() == 'cross':
                island = self.chain_manager.get_island(
                    msg.header['target_chain_id']
                )
                if island is not None:
                    msg.set_type('normal')
                    self.send(island, msg)
                else:
                    lane = self.chain_manager.get_lane(
                        self.router.next_jump(request.tx)
                    )
                    if lane is not None and not isinstance(lane, list):
                        self.send(lane, msg)
                    else:
                        log.error(f'No chain to transfer tx: {msg.get_json()}')
            elif msg.get_type() == 'normal':
                log.debug('normal message')
            elif msg.get_type() == 'graph':
                log.debug('graph message')
            elif msg.get_type() == 'validate':
                log.debug('validate message')
            else:
                log.debug('unknown message')
