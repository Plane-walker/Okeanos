__all__ = [
    'Router',
]


# from interface.bci.bci_pb2_grpc import LaneStub
import os
import random
import time
import yaml
import uuid
import json
import requests
from threading import Thread
from interface.common.id_pb2 import Chain
from google.protobuf.json_format import MessageToJson
from interface.dci.dci_pb2 import (
    RequestRouterInfo,
    ResponseRouterInfo,
    RequestRouterPathCallback,
    ResponseRouterPathCallback,
    RequestRouterTransmit,
    ResponseRouterTransmit,
)
from interface.bci.bci_pb2 import (
    RequestGossipQueryPath,
    RequestGossipCallBack,
)
from enum import Enum, unique
from log import log


@unique
class DciResCode(Enum):
    OK = 0
    FAIL = 1


class Router:

    def __init__(self, config_path, chain_manager) -> None:
        self.chain_manager = chain_manager
        self.config = None

        self.lane_ids = set()
        self.island_id = None

        # Route table is a dict
        # whose key is target chain_id of island in str type and
        # whose value is chain_id of lane in str type.
        self.route = {}

        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.config = config['router']
        route_path = os.path.join(os.path.dirname(config_path), self.config['route_path'])
        if os.path.exists(route_path):
            with open(route_path) as file:
                self.route = yaml.load(file, Loader=yaml.Loader)
        # Thread(target=self.periodical_gossip, daemon=True).start()

    def import_chain_id(self):
        lanes = self.chain_manager.get_lane()
        for lane in lanes:
            self.lane_ids.add(lane.chain_id)
        self.island_id = self.chain_manager.get_island()[0].chain_id

    def periodical_gossip(self):
        self.import_chain_id()
        while True:
            log.info('Periodical Gossip . . .')
            identifier = uuid.uuid4().hex
            target = Chain(identifier=identifier)
            self.gossip(Chain(identifier=self.island_id), target, self.config['ttl'], [])
            time.sleep(self.config['periodical_gossip_interval'])

    def next_jump(self, target: Chain):
        self.import_chain_id()
        if target.identifier not in self.route.keys():
            ttl = self.config['ttl']
            while True:
                paths = []
                code = self.gossip(Chain(identifier=self.island_id), target, ttl, paths)
                if code is None:
                    return None
                ttl += self.config['ttl']
        return self.route[target.identifier]

    def gossip(self, source: Chain, target: Chain, ttl, paths: list):
        self.import_chain_id()
        num_of_neighbours = len(self.lane_ids)
        if num_of_neighbours < self.config['min_router_chain']:
            return None
        selecteds = None
        if num_of_neighbours < self.config['min_search']:
            selecteds = self.lane_ids
        else:
            selecteds = random.sample(list(self.lane_ids), self.config['min_search'])
        log.info(selecteds)
        self.transmit_to_others(selecteds, source, target, ttl, paths=paths.copy())
        return DciResCode.OK.value

    def transmit_to_others(self, lane_ids, source: Chain, target: Chain, ttl, paths: list):
        """Transmit gossip message to each route chain

        Args:
            lane_ids (str): Route chains selected to gossip
            source (Chain): The source data chain who sent gossip
            target (Chain): The target data chain who will been found
            ttl (int): ttl
            paths (list): The list of route path consists of route chain id
        """
        self.import_chain_id()
        for lane_id in lane_ids:
            if len(paths) > 0 and lane_id == paths[-1]:
                continue
            paths.append(lane_id)
            # req = RequestGossipQueryPath(
            #     target=target, source=source, ttl=ttl)
            # req.route_chains.extend([path for path in paths])
            tx_json = {"target":target.identifier, "source":source.identifier, "ttl":ttl, "paths":paths}
            log.info(tx_json)
            params = (
                ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
            )
            log.info(f'Connect to http://localhost:{self.chain_manager.get_lane(lane_id).rpc_port}')
            response = requests.get(f'http://localhost:{self.chain_manager.get_lane(lane_id).rpc_port}/broadcast_tx_commit', params=params)
            log.info(response)

    def callback_to_finder(self, source: Chain, target: Chain, paths: list):
        """
        :source is data chain who has been found
        :target is data chain who sent gossip first
        """
        self.import_chain_id()
        for lane_id in self.lane_ids:
            if len(paths) > 0 and lane_id == paths[-1]:
                # The source in RequestGossipCallBack is who has been found and
                # then sends callback. And the target in RequestGossipCallBack
                # is who sent gossip first and waiting now.
                # req = RequestGossipCallBack(
                #     target=target, source=source)
                # req.route_chains.extend([path for path in paths])
                # with grpc.insecure_channel('localhost:'+str(lane.port)) as channel:
                #     log.info('Connect to ', channel)
                #     stub = LaneStub(channel)
                #     res = stub.GossipCallBack(req)
                #     log.info(res)
                tx_json = {'target': target, 'source': source, 'paths': paths[:-1]}
                params = (
                    ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                )
                log.info('0x' + json.dumps(tx_json).encode('utf-8').hex())
                log.info(f'Connect to http://localhost:{self.chain_manager.get_lane(lane_id).rpc_port}')
                response = requests.get(f'http://localhost:{self.chain_manager.get_lane(lane_id).rpc_port}/broadcast_tx_commit', params=params)
                log.info(response)

    def info(self, req: RequestRouterInfo):
        self.import_chain_id()
        res = ResponseRouterInfo(code=DciResCode.OK.value,
                                 data=(
                                     'Route Table:\n'+str(self.route)
                                 ).encode('utf-8'),
                                 info='Return route table info!')
        yield res

    def transmit(self, req: RequestRouterTransmit):
        yield ResponseRouterTransmit(code=DciResCode.OK.value, info='')
        self.import_chain_id()
        paths = [path.identifier for path in req.paths]
        for lane_id in self.lane_ids:
            if lane_id == paths[-1]:
                self.route[req.source.identifier] = paths[-1]
        if req.ttl > 0:
            if req.target.identifier == self.island_id:
                self.callback_to_finder(req.target, req.source, paths)
            elif req.target.identifier in self.route.keys():
                self.callback_to_finder(req.target, req.source, paths)
            else:
                self.gossip(req.source, req.target, ttl=req.ttl-1, paths=paths)

    def callback(self, req: RequestRouterPathCallback):
        yield ResponseRouterPathCallback(code=DciResCode.OK.value, info='')
        self.import_chain_id()
        paths = [path.identifier for path in req.paths]
        for lane_id in self.lane_ids:
            if lane_id == paths[-1]:
                self.route[req.source.identifier] = paths[-1]
        if req.target.identifier != self.island_id:
            self.callback_to_finder(req.source, req.target, paths[:-1])
        log.debug(self.route)
