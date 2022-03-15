__all__ = ['CrossChainCommunicationProtocol']

from enum import Enum, unique
import json
import yaml
import requests
from interface.dci import dci_pb2
import base64
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
        self._config_path = config_path

    def send(self, chain, msg):
        if not self.router.judge_validator(msg):
            return
        params = (('tx', msg.get_hex()), )
        log.info(f'Send to {chain.chain_type}: '
                 f'{chain.chain_name}({chain.chain_id}) with {msg.get_json()}')
        response = requests.get(
            f'http://localhost:{chain.rpc_port}/broadcast_tx_commit',
            params=params)
        log.info(f'{chain.chain_name} return: {response}')

    def deliver_tx(self, request: dci_pb2.RequestDeliverTx):
        try:
            log.debug('prepare msg . . .')
            msg = Message.from_req(request)
            if msg is None:
                raise ValueError('msg is None')
            if msg.get_type() not in Message.types:
                raise ValueError('msg type is not one of %s' % Message.types)
        except Exception as exception:
            log.error(repr(exception))
            yield dci_pb2.ResponseDeliverTx(code=TxDeliverCode.FAIL.value)
        else:
            yield dci_pb2.ResponseDeliverTx(code=TxDeliverCode.Success.value)
            log.debug(f'Recieve msg: {msg.get_json()}')
            if msg.get_type() == 'route':
                self.router.receiver(request.tx)
            elif msg.get_type() == 'cross':
                island = self.chain_manager.get_island(
                    msg.header['target_chain_id'])
                if island is not None:
                    msg.set_type('normal')
                    self.send(island, msg)
                else:
                    lane = self.chain_manager.get_lane(
                        self.router.next_jump(request.tx))
                    if lane is not None and not isinstance(lane, list):
                        self.send(lane, msg)
                    else:
                        log.error(f'No chain to transfer tx: {msg.get_json()}')

    def query(self, request):
        yield dci_pb2.ResponseQuery(code=TxDeliverCode.Success.value)
        # if not self.router.judge_validator(Message.from_req(request)):
        #     return
        tx_json = json.loads(request.tx.decode('utf-8'))
        island = self.chain_manager.get_island(tx_json['header']['target_chain_id'])
        if island is not None:
            tx_json['header']['type'] = 'normal'
            params = (
                ('data', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
            )
            log.info(f'Send query message to {island.chain_type}: {island.chain_name}({island.chain_id})')
            response = requests.get(f'http://localhost:{island.rpc_port}/abci_query', params=params)
            log.info(f'{island.chain_name} return: {response}')
            with open(self._config_path) as file:
                config = yaml.load(file, Loader=yaml.Loader)
            message = {
                "header": {
                    "type": "cross",
                    "ttl": tx_json['header']['ttl'],
                    "index": tx_json['header']['index'],
                    "paths": [],
                    "source_chain_id": tx_json['header']['target_chain_id'],
                    "target_chain_id": tx_json['header']['source_chain_id'],
                    "auth": {
                        "app_id": config['app']['app_id']
                    }
                },
                "body": {
                    "key": f"response_for_query_{tx_json['body']['query']}",
                    "value": json.loads(base64.b64decode(json.loads(response.text)['result']['response']['value'].encode('utf-8')).decode('utf-8'))
                }
            }
            params = (
                ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
            )
            log.info(f'Send cross query response to {island.chain_type}: {island.chain_name}({island.chain_id})')
            response = requests.get(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params=params)
        else:
            lane = self.chain_manager.get_lane(self.router.next_jump(request.tx))
            if lane is not None and not isinstance(lane, list):
                log.info(f'Send to {lane.chain_type}: {lane.chain_name}({lane.chain_id})')
                params = (
                    ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                )
                response = requests.get(f'http://localhost:{lane.rpc_port}/broadcast_tx_commit', params=params)
                log.info(f'{lane.chain_name} return: {response}')
            else:
                log.error(f'No chain to transfer tx')
