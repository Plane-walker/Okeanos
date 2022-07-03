__all__ = [
    'CrossChainCommunicationProtocol'
]

from enum import Enum, unique
import json
import yaml
import requests
import hashlib
from interface.dci import dci_pb2
import base64
from log import log
import sys
from dock.router import Router
import socket


@unique
class TxDeliverCode(Enum):
    Success = 0
    FAIL = 1


class CrossChainCommunicationProtocol:

    def __init__(self, config_path, chain_manager, pool):
        self.lane = None
        self.pool = pool
        self.router = Router(config_path, chain_manager, self.pool)
        self.chain_manager = chain_manager
        self._config_path = config_path

    def rpc_request_async(self, url, params):
        def rpc_request():
            requests.get(url, params=params)
        self.pool.submit(rpc_request)

    def dispatch_async(self, request):
        def dispatch():
            tx_json = json.loads(request.tx.decode('utf-8'))
            lane = self.chain_manager.get_lane(self.router.next_jump(request.tx))
            if lane is not None and not isinstance(lane, list):
                if len(tx_json['header']['cross']['paths']) == 0 or self.router.island_id != tx_json['header']['cross']['paths'][0][1]:
                    tx_json['header']['cross']['paths'] = [(lane.chain_id, self.router.island_id)]
                    params = (
                        ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                    )
                    log.info(f'Send to {lane.chain_name}: {lane.chain_id}')
                    self.rpc_request_async(f'http://localhost:{lane.rpc_port}/broadcast_tx_commit', params)
                else:
                    log.debug(f'Ignore the same message {tx_json}')
            else:
                log.warning(f"No chain to transfer tx: {str(json.dumps(tx_json).encode('utf-8'))}")
        self.pool.submit(dispatch)

    def deliver_tx(self, request: dci_pb2.RequestDeliverTx):
        try:
            tx_json = json.loads(request.tx.decode('utf-8'))
            if tx_json['header']['type'] == 'route':
                log.debug(f'Route tx: {tx_json}')
                self.router.receiver(request.tx)
            elif tx_json['header']['type'] == 'cross_move_source':
                log.debug(f'Cross write tx: {tx_json}')
                island = self.chain_manager.get_island(tx_json['header']['cross']['target_chain_id'])
                if island is not None:
                    tx_json['header']['type'] = 'cross_move_target'
                    params = (
                        ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                    )
                    log.info(f'Send to {island.chain_name}: {island.chain_id}')
                    self.rpc_request_async(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params)
                else:
                    self.dispatch_async(request)
            return dci_pb2.ResponseDeliverTx(code=TxDeliverCode.Success.value)
        except Exception as exception:
            log.error(repr(exception))
            return dci_pb2.ResponseDeliverTx(code=TxDeliverCode.FAIL.value)

    # Judge the minimum editing distance validator
    def judge_validator(self, tx_json) -> bool:
        # obtain the island_id
        island = self.chain_manager.get_island()[0]

        # sha256 the tx
        tx = hashlib.sha256(
            ('0x' + json.dumps(tx_json).encode('utf-8').hex()).encode('utf-8')
        ).hexdigest()[:20]

        response = requests.get(f'http://localhost:{island.rpc_port}/validators').json()
        min_dis = sys.maxsize
        target = response['result']['validators'][0]['address']
        for validator in response['result']['validators']:
            distance = self.min_distance(validator['address'], tx)
            if distance < min_dis:
                target = validator['address']
                min_dis = distance
        # obtain the address
        response = requests.get(
            f'http://localhost:{island.rpc_port}/status').json()
        self_address = response['result']['validator_info']['address']
        return self_address == target

    def min_distance(self, validator: str, tx: str) -> int:
        validator = validator.upper()
        tx = tx.upper()
        n = len(validator)
        m = len(tx)
        if n * m == 0:
            return n + m
        D = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            D[i][0] = i
        for j in range(m + 1):
            D[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                left = D[i - 1][j] + 1
                down = D[i][j - 1] + 1
                left_down = D[i - 1][j - 1]
                if validator[i - 1] != tx[j - 1]:
                    left_down += 1
                D[i][j] = min(left, down, left_down)
        return D[n][m]

    def query(self, request):
        try:
            tx_json = json.loads(request.tx.decode('utf-8'))
            if self.judge_validator(tx_json):
                island = self.chain_manager.get_island(tx_json['header']['target_chain_id'])
                if island is not None:
                    if tx_json['header']['type'] == 'cross_read':
                        tx_json['header']['type'] = 'read_full'
                        params = (
                            ('data', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                        )
                        log.info(f'Send query message to {island.chain_name}({island.chain_id})')
                        response = requests.get(f'http://localhost:{island.rpc_port}/abci_query', params=params)
                        value = json.loads(base64.b64decode(json.loads(response.text)['result']['response']['value'].encode('utf-8')).decode('utf-8'))
                        log.info(f'{island.chain_name} return: {response}')
                        message = {
                            "header": {
                                "type": "cross_write",
                                "ttl": tx_json['header']['ttl'],
                                "paths": [],
                                "source_chain_id": tx_json['header']['target_chain_id'],
                                "target_chain_id": tx_json['header']['source_chain_id'],
                                "auth": {
                                    "app_id": value['keeper']['app_id'],
                                    "app_info": value['keeper']['app_info']
                                }
                            },
                            "body": {
                                "key": f"response_for_query_{tx_json['body']['key']}",
                                "value": value['value']
                            }
                        }
                        params = (
                            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
                        )
                        log.info(f'Send cross query response to {island.chain_name}({island.chain_id})')
                        self.rpc_request_async(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params)
                    elif tx_json['header']['type'] == 'cross_graph':
                        tx_json['header']['type'] = 'graph'
                        params = (
                            ('data', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                        )
                        log.info(f'Send query message to {island.chain_name}({island.chain_id})')
                        response = requests.get(f'http://localhost:{island.rpc_port}/abci_query', params=params)
                        log.info(f'{island.chain_name} return: {response}')
                        with open(self._config_path) as file:
                            config = yaml.load(file, Loader=yaml.Loader)
                        message = {
                            "header": {
                                "type": "cross_write",
                                "ttl": tx_json['header']['ttl'],
                                "paths": [],
                                "source_chain_id": tx_json['header']['target_chain_id'],
                                "target_chain_id": tx_json['header']['source_chain_id'],
                                "auth": {
                                    "app_id": config['app']['app_id'],
                                    "app_info": ""
                                }
                            },
                            "body": {
                                "key": f"response_for_query_{tx_json['body']['key']}",
                                "value": json.loads(base64.b64decode(json.loads(response.text)['result']['response']['value'].encode('utf-8')).decode('utf-8'))
                            }
                        }
                        params = (
                            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
                        )
                        log.info(f'Send cross query response to {island.chain_name}({island.chain_id})')
                        self.rpc_request_async(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params)
                    elif tx_json['header']['type'] == 'join':
                        with open(self._config_path) as file:
                            config = yaml.load(file, Loader=yaml.Loader)
                        if config['app']['fixed_server_ip']:
                            ip = config['app']['server_ip']
                        else:
                            hostname = socket.gethostname()
                            ip = socket.gethostbyname(hostname)
                        join_info = {
                            "island": [f'{ip}:{island.rpc_port}' for island in self.chain_manager.get_island()],
                            "lane": [f'{ip}:{lane.rpc_port}' for lane in self.chain_manager.get_lane()]
                        }
                        message = {
                            "header": {
                                "type": "cross_write",
                                "ttl": tx_json['header']['ttl'],
                                "paths": [],
                                "source_chain_id": tx_json['header']['target_chain_id'],
                                "target_chain_id": tx_json['header']['source_chain_id'],
                                "auth": {
                                    "app_id": config['app']['app_id'],
                                    "app_info": ""
                                }
                            },
                            "body": {
                                "key": f"response_for_query_join_{tx_json['header']['target_chain_id']}",
                                "value": join_info

                            }
                        }
                        params = (
                            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
                        )
                        log.info(f'Send cross query response to {island.chain_name}({island.chain_id})')
                        self.rpc_request_async(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params)
                else:
                    self.dispatch_async(request)
            return dci_pb2.ResponseQuery(code=TxDeliverCode.Success.value)
        except Exception as exception:
            log.error(repr(exception))
            return dci_pb2.ResponseQuery(code=TxDeliverCode.FAIL.value)
