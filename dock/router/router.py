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
        self.node_id = None
        self.island_id = None
        self.config = None

        # Key is the id of lane
        # Value is the object of BaseChain for lane
        self.lanes = {}

        # Route table is a dict whose key is target id in str type and
        # whose value is Lane Chain.
        self.route = {}

        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.config = config['router']
        self.chain_num = len(config['chain_manager']['chain'])
        route_path = os.path.join(os.path.dirname(config_path), self.config['route_path'])
        if os.path.exists(route_path):
            with open(route_path) as file:
                self.route = yaml.load(file, Loader=yaml.Loader)
        # Thread(target=self.periodical_gossip, daemon=True).start()

    def import_chain_id(self):
        if len(self.chain_manager.chains) == self.chain_num:
            return
        while len(self.chain_manager.chains) < self.chain_num:
            log.info("Waiting for chain manager to be ready")
            time.sleep(1)
        for chain_id in self.chain_manager.chains.keys():
            if 'lane' in self.chain_manager.chains[chain_id].chain_name:
                self.lanes[chain_id] = self.chain_manager.chains[chain_id]
            else:
                self.island_id = chain_id

    def periodical_gossip(self):
        self.import_chain_id()
        while True:
            log.info('Periodical Gossip . . .')
            identifier = uuid.uuid4().hex
            target = Chain(identifier=identifier)
            self.gossip(Chain(identifier=self.island_id), target, self.config['ttl'], [])
            time.sleep(self.config['periodical_gossip_interval'])

    def next_jump(self, target: Chain) -> Chain:
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
        num_of_neighbours = len(self.lanes)
        log.info(self.lanes)
        if num_of_neighbours < self.config['min_router_chain']:
            return None
        selecteds = None
        if num_of_neighbours < self.config['min_search']:
            selecteds = self.lanes.keys()
        else:
            selecteds = random.sample(self.lanes.keys(), self.config['min_search'])
        log.info(selecteds)
        self.transmit_to_others(selecteds, source, target, ttl, paths=paths.copy())
        return DciResCode.OK.value

    def transmit_to_others(self, lane_ids, source: Chain, target: Chain, ttl, paths: list):
        """Transmit gossip message to each route chain

        Args:
            lanes (list(Lane)): Route chains selected to gossip
            source (Chain): The source data chain who sent gossip
            target (Chain): The target data chain who will been found
            ttl (int): ttl
            paths (list): The list of route path consists of route chain id
        """
        for lane_id in lane_ids:
            if len(paths) > 0 and lane_id == paths[-1]:
                continue
            paths.append(Chain(identifier=lane_id))
            req = RequestGossipQueryPath(
                target=target, source=source, ttl=ttl)
            req.route_chains.extend([path for path in paths])
            tx_json = json.loads(MessageToJson(req))
            log.info(tx_json)
            params = (
                ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
            )
            log.info('0x' + json.dumps(tx_json).encode('utf-8').hex())
            log.info(f'Connect to http://localhost:{self.lanes[lane_id].rpc_port}')
            response = requests.get(f'http://localhost:{self.lanes[lane_id].rpc_port}/broadcast_tx_commit', params=params)
            log.info(response)

    def callback_to_finder(self, source: Chain, target: Chain, paths: list):
        """
        :source is data chain who has been found
        :target is data chain who sent gossip first
        """
        for lane_id in self.lanes.keys():
            if len(paths) > 0 and lane_id == paths[-1]:
                # The source in RequestGossipCallBack is who has been found and
                # then sends callback. And the target in RequestGossipCallBack
                # is who sent gossip first and waiting now.
                req = RequestGossipCallBack(
                    target=target, source=source)
                req.route_chains.extend([path for path in paths])
                # with grpc.insecure_channel('localhost:'+str(lane.port)) as channel:
                #     log.info('Connect to ', channel)
                #     stub = LaneStub(channel)
                #     res = stub.GossipCallBack(req)
                #     log.info(res)
                tx_json = json.loads(MessageToJson(req))
                params = (
                    ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
                )
                log.info('0x' + json.dumps(tx_json).encode('utf-8').hex())
                log.info(f'Connect to http://localhost:{self.lanes[lane_id].rpc_port}')
                response = requests.get(f'http://localhost:{self.lanes[lane_id].rpc_port}/broadcast_tx_commit', params=params)
                log.info(response)

    def info(self, req: RequestRouterInfo) -> ResponseRouterInfo:
        res = ResponseRouterInfo(code=DciResCode.OK.value,
                                 data=(
                                     'Route Table:\n'+str(self.route)
                                 ).encode('utf-8'),
                                 info='Return route table info!')
        return res

    def transmit(self, req: RequestRouterTransmit) -> ResponseRouterTransmit:
        yield ResponseRouterTransmit(code=DciResCode.OK.value)
        paths = req.paths
        self.route[req.source.identifier] = paths[-1]
        if req.ttl <= 0:
            return ResponseRouterTransmit(code=DciResCode.OK.value)
        if req.target.identifier == self.island_id:
            self.callback_to_finder(req.target, req.source, paths)
        elif req.target.identifier in self.route:
            self.callback_to_finder(req.target, req.source, paths)
        else:
            self.gossip(req.source, req.target, ttl=req.ttl-1, paths=paths)

    def callback(self, req: RequestRouterPathCallback) -> ResponseRouterPathCallback:
        yield ResponseRouterPathCallback(code=DciResCode.OK.value)
        paths = req.paths
        self.route[req.source.identifier] = paths[-1]
        for lane in self.lanes:
            if req.target.identifier == lane.identifier:
                return ResponseRouterPathCallback(code=DciResCode.OK.value)
        self.callback_to_finder(req.source, req.target, paths[:-1])
