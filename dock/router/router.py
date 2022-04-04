__all__ = [
    'Router',
]

import random
import requests
import yaml
import json
import os
import uuid
import time
import sys
import base64
import hashlib
import datetime
from enum import Enum, unique
from log import log
from .package import RouteMessage


@unique
class DciResCode(Enum):
    OK = 0
    FAIL = 1


class Router:

    def __init__(self, config_path, chain_manager, pool):
        self.island_id = None
        self.lane_ids = set()

        self.chain_manager = chain_manager
        self.pool = pool
        self.config = None

        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.config = config['router']
        self.config['app'] = config['app']
        route_path = os.path.join(os.path.dirname(config_path),
                                  self.config['route_path'])
        # Thread(target=self.periodical_gossip, daemon=True).start()

    def import_chain_id(self):
        lanes = self.chain_manager.get_lane()
        for lane in lanes:
            self.lane_ids.add(lane.chain_id)
        self.island_id = self.chain_manager.get_island()[0].chain_id

    def search_island_router(self, key):
        island = self.chain_manager.get_island()[0]
        message = {
            "header": {
                "type": "read",
                "ttl": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": self.config['app']['app_id'],
                    "app_info": ""
                }
            },
            "body": {
                "key": key
            }
        }
        params = (('data', '0x' + json.dumps(message).encode('utf-8').hex()), )
        log.debug(f'Search island to {key} through http://localhost:{island.rpc_port}')
        url = f'http://localhost:{island.rpc_port}/abci_query'
        response = requests.get(url, params=params)
        log.debug(f'Get router response {response.json()}')
        if 'code' in response.json()['result']['response'] and response.json()['result']['response']['code'] == 0:
            return base64.b64decode(response.json()['result']['response']['value'].encode('utf-8')).decode('utf-8')[1:-1]
        return None


    def insert_island_router(self, key, value):
        island = self.chain_manager.get_island()[0]
        island_id = island.chain_id
        message = {
            "header": {
                "type": "write",
                "ttl": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": self.config['app']['app_id'],
                    "app_info": ""
                }
            },
            "body": {
                "key": key,
                "value": value
            }
        }
        params = (('tx', '0x' + json.dumps(message).encode('utf-8').hex()), )
        log.debug(f'Insert island to {key} by http://localhost:{island.rpc_port} with {message}')
        response = requests.get(
            f'http://localhost:'
            f'{self.chain_manager.get_lane(island_id).rpc_port}'
            f'/broadcast_tx_commit',
            params=params)
        log.debug(f"Get router response {response.json()['result']}")
        log.info(f'Update router {key}: {value}')
        # def rpc_request():
        #     response = requests.get(
        #         f'http://localhost:'
        #         f'{self.chain_manager.get_lane(island_id).rpc_port}'
        #         f'/broadcast_tx_commit',
        #         params=params)
        #     log.info(f'Get router from {island}: {response}')
        # self.pool.submit(rpc_request)

    def periodical_gossip(self):
        while True:
            try:
                log.info('Periodical Gossip . . .')
                target = uuid.uuid4().hex
                package = RouteMessage.from_data(self.island_id, target, self.config['app']['app_id'],
                                                 '', 'route', self.config['ttl'])
                package.init_paths()
                self.gossip(package)
                time.sleep(self.config['periodical_gossip_interval'])
            except Exception as exception:
                log.error(f'Periodical Gossip Error: {repr(exception)}')

    def next_jump(self, tx):
        try:
            self.import_chain_id()
            package = RouteMessage.from_tx(tx)
            ttl = self.config['ttl']
            while True:
                value = self.search_island_router(package.target_id())
                if value is not None:
                    return value
                log.info(f'Searching {package.target_id()}')
                if ttl > self.config['max_ttl']:
                    return None
                package.set_ttl(ttl)
                if package.get_paths_copy() is None:
                    package.init_paths()
                log.debug(f'Gossip {package.get_json()}')
                self.gossip(package)
                start_time = datetime.datetime.now()
                timeout = ttl * 2
                while True:
                    value = self.search_island_router(package.target_id())
                    if value is not None:
                        return value
                    if (datetime.datetime.now() - start_time).seconds > timeout:
                        break
                    time.sleep(1)
                ttl += self.config['ttl']
        except Exception as exception:
            log.error(f'Next Jump Error: {repr(exception)}')
            return None

    def gossip(self, package: RouteMessage):
        num_of_neighbours = len(self.lane_ids)
        selecteds = None
        if num_of_neighbours < self.config['min_search']:
            selecteds = list(self.lane_ids)
        else:
            selecteds = random.sample(list(self.lane_ids),
                                      self.config['min_search'])
        log.debug(f'Select {selecteds}')
        for selected_id in selecteds:
            paths = package.get_paths_lanes_copy()
            if paths is not None and selected_id in paths:
                continue
            package.append_path(selected_id, self.island_id)
            self.sender(selected_id, package)
            package.pop_path()
        return DciResCode.OK.value

    def sender(self, lane_id, package: RouteMessage):
        package.set_type('route')
        if not self.judge_validator(package):
            return
        log.debug(f'Connect to http://localhost:'
                 f'{self.chain_manager.get_lane(lane_id).rpc_port} '
                 f'with {package.get_json()}')
        params = (('tx', package.get_hex()), )

        def rpc_request():
            response = requests.get(
                f'http://localhost:'
                f'{self.chain_manager.get_lane(lane_id).rpc_port}'
                f'/broadcast_tx_commit',
                params=params)
            log.info(f'Get response from {lane_id}: {response}')
        self.pool.submit(rpc_request)

    # Judge the minimum editing distance validator
    def judge_validator(self, package) -> bool:
        # obtain the island_id
        island = self.chain_manager.get_island()[0]
        # sha256 the tx
        tx = hashlib.sha256(package.get_hex().encode('utf-8')).hexdigest()[:20]
        response = requests.get(
            f'http://localhost:{island.rpc_port}/validators').json()
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

    def receiver(self, tx):
        self.import_chain_id()
        try:
            package = RouteMessage.from_tx(tx)
            if package.source_id() == self.island_id:
                log.debug(f'Ignore from self {package.get_json()}')
                return
            log.info(f'Route from {package.source_id()} to {package.target_id()}')
            if package.is_transmit():
                log.debug(f'Transmit {package.get_json()}')
                self.transmit(package)
            elif package.is_callback():
                log.debug(f'Callback {package.get_json()}')
                self.callback(package)
            else:
                log.debug('Ignore when ttl == 0')
        except Exception as exception:
            log.error(f'Receiver Error: {repr(exception)}')

    def transmit(self, package: RouteMessage):

        if self.island_id in package.get_paths_islands_copy():
            log.debug(f'Ignore ring route {package.get_json()}')
            return

        value = self.search_island_router(package.source_id())
        if package.last_path_lane() in self.lane_ids and value is None:
            self.insert_island_router(package.source_id(), package.last_path_lane())

        if package.get_ttl() == 0:
            return

        value = self.search_island_router(package.target_id())
        if package.target_id() == self.island_id or value is not None:
            package.to_callback()
            if package.last_path_lane() in self.lane_ids:
                self.sender(package.last_path_lane(), package)
        else:
            package.reduce_ttl()
            self.gossip(package)

    def callback(self, package: RouteMessage):

        index = package.get_island_index(self.island_id)
        if index == -1:
            log.debug(f'Not found {self.island_id} in {package.get_json()}')
            return

        lane_id, _ = package.get_path(index)[0], package.get_path(index)[1]
        value = self.search_island_router(package.source_id())
        if value is None:
            log.debug(f'Update router {package.source_id()}: {lane_id}')
            self.insert_island_router(package.source_id(), lane_id)
        else:
            log.debug(f'Ignore ring in callback')
            return

        if package.target_id() == self.island_id:
            log.debug(f'Finish callback {package.get_json()}')
            return

        index -= 1
        path = package.get_path(index)
        if path is None:
            log.debug(f'Not found the {index} path {package.get_json()}')
            return
        lane_id, _ = path[0], path[1]
        self.sender(lane_id, package)
