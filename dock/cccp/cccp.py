__all__ = [
    'CrossChainCommunicationProtocol'
]

from enum import Enum, unique
import json
import yaml
import requests
import hashlib
from interface.dci import dci_pb2
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
            elif tx_json['header']['type'] == 'cross_write':
                log.debug(f'Cross write tx: {tx_json}')
                island = self.chain_manager.get_island(tx_json['header']['cross']['target_chain_id'])
                if island is not None:
                    tx_json['header']['type'] = 'write'
                    params = (
                        ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                    )
                    log.info(f'Send to {island.chain_name}: {island.chain_id}')
                    self.rpc_request_async(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params)
                else:
                    self.dispatch_async(request)
            elif tx_json['header']['type'] == 'unlock':
                log.debug(f'Cross write tx: {tx_json}')
                island = self.chain_manager.get_island(tx_json['header']['cross']['target_chain_id'])
                if island is not None:
                    params = (
                        ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                    )
                    log.info(f'Send to {island.chain_name}: {island.chain_id}')
                    self.rpc_request_async(f'http://localhost:{island.rpc_port}/broadcast_tx_commit', params)
                else:
                    self.dispatch_async(request)
            elif tx_json['header']['type'] == 'join':
                log.debug(f'Cross write tx: {tx_json}')
                island = self.chain_manager.get_island(tx_json['header']['cross']['target_chain_id'])
                if island is not None:
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
                            "cross": {
                                "ttl": tx_json['header']['cross']['ttl'],
                                "paths": [],
                                "source_chain_id": tx_json['header']['cross']['target_chain_id'],
                                "source_node_id": tx_json['header']['cross']['target_node_id'],
                                "source_info": tx_json['header']['cross']['target_info'],
                                "target_chain_id": tx_json['header']['cross']['source_chain_id'],
                                "target_node_id": tx_json['header']['cross']['source_node_id'],
                                "target_info": tx_json['header']['cross']['source_info'],
                            },
                            "timestamp": tx_json['header']['timestamp']
                        },
                        "body": {
                            "key": f"_join_info_{tx_json['header']['cross']['target_chain_id']}",
                            "value": join_info
                        }
                    }
                    request.tx = json.dumps(message).encode('utf-8')
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
