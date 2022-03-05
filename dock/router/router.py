__all__ = [
    'Router',
]


import random
import requests
import yaml
import os
import uuid
import time
from enum import Enum, unique
from interface.sci.types.types_pb2 import Data
from log import log
from .package import DataPackage


@unique
class DciResCode(Enum):
    OK = 0
    FAIL = 1


class Router:

    def __init__(self, config_path, chain_manager):
        self.island_id = None
        self.lane_ids = set()

        self.router = {}

        self.chain_manager = chain_manager
        self.config = None

        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.config = config['router']
        route_path = os.path.join(os.path.dirname(config_path),
                                  self.config['route_path'])
        if os.path.exists(route_path):
            with open(route_path) as file:
                self.router = yaml.load(file, Loader=yaml.Loader)
        # Thread(target=self.periodical_gossip, daemon=True).start()

    def import_chain_id(self):
        lanes = self.chain_manager.get_lane()
        for lane in lanes:
            self.lane_ids.add(lane.chain_id)
        self.island_id = self.chain_manager.get_island()[0].chain_id

    def periodical_gossip(self):
        while True:
            try:
                log.info('Periodical Gossip . . .')
                target = uuid.uuid4().hex
                package = DataPackage.from_data(
                    self.island_id, target, self.config['ttl']
                )
                package.init_paths()
                self.gossip(package)
                time.sleep(self.config['periodical_gossip_interval'])
            except Exception as exception:
                log.error(f'Periodical Gossip Error: {repr(exception)}')

    def next_jump(self, tx):
        self.import_chain_id()
        try:
            package = DataPackage.from_tx(tx)
            ttl = self.config['ttl']
            while True:
                if package.target_id() in self.router:
                    return self.router[package.target_id()]
                log.info(f'Searching with {package.get_json()}')
                if ttl > self.config['max_ttl']:
                    return None
                package.set_ttl(ttl)
                if package.get_paths_copy() is None:
                    package.init_paths()
                code = self.gossip(package)
                if code is None:
                    return None
                ttl += self.config['ttl']
        except Exception as exception:
            log.error(f'Next Jump Error: {repr(exception)}')
            return None

    def gossip(self, package: DataPackage):
        num_of_neighbours = len(self.lane_ids)
        selecteds = None
        if num_of_neighbours < self.config['min_search']:
            selecteds = list(self.lane_ids)
        else:
            selecteds = random.sample(
                list(self.lane_ids), self.config['min_search']
            )
        log.debug(f'Select {selecteds}')
        for selected_id in selecteds:
            reached = False
            paths = package.get_paths_copy()
            if paths is not None:
                for path in paths:
                    if path == selected_id:
                        reached = True
                        break
                if reached:
                    continue
            package.append_path(selected_id)
            self.sender(selected_id, package)
            package.pop_path()
        return DciResCode.OK.value

    def sender(self, lane_id, package: DataPackage):
        package.set_type('route')
        log.info(
            f'Connect to http://localhost:'
            f'{self.chain_manager.get_lane(lane_id).rpc_port} '
            f'with {package.get_json()}'
        )
        params = (
            ('tx', package.get_hex()),
        )
        response = requests.get(
            f'http://localhost:'
            f'{self.chain_manager.get_lane(lane_id).rpc_port}'
            f'/broadcast_tx_commit',
            params=params
        )
        log.info(f'Get response code: {response}')

    def receiver(self, tx):
        self.import_chain_id()
        try:
            # package = DataPackage.from_req(req)
            package = DataPackage.from_tx(tx)
            log.info(f'Receive {package.get_json()}')
            if package.source_id() == self.island_id:
                return
            if package.is_transmit():
                self.transmit(package)
            elif package.is_callback():
                self.callback(package)
            else:
                log.info('Ignore when ttl == 0')
        except Exception as exception:
            log.error(f'Receiver Error: {repr(exception)}')

    def transmit(self, package):
        log.debug('Transmit . . .')
        if package.last_path() in self.lane_ids:
            self.router[package.source_id()] = package.last_path()
        if package.get_ttl() == 0:
            return
        if package.target_id() == self.island_id or \
           package.target_id() in self.router.keys():
            package.to_callback()
            for lane_id in self.lane_ids:
                if lane_id == package.last_path():
                    self.sender(lane_id, package)
        else:
            package.reduce_ttl()
            self.gossip(package)

    def callback(self, package):
        log.debug('Callback . . .')
        index = package.get_ttl()
        if package.target_id() == self.island_id:
            self.router[package.source_id()] = package.get_path(index)
            return

        if package.get_path(index) not in self.lane_ids:
            return

        if index == -1:
            self.router[package.source_id()] = package.last_path()
        else:
            last = index
            while index < 0:
                index += 1
                if package.get_path(index) in self.lane_ids:
                    last = index
            if last == package.get_ttl() and \
               package.get_path(last) in self.lane_ids:
                self.router[package.source_id()] = package.get_path(last)

        package.reduce_ttl()
        if package.get_path(package.get_ttl()) is None or \
           package.get_path(package.get_ttl()) not in self.lane_ids:
            return
        self.sender(package.get_path(package.get_ttl()), package)
