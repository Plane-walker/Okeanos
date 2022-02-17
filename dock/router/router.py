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

    def __init__(self, config_path) -> None:
        self.node_id = '0'
        self.data_chain_id = '0'
        # Key is the id of Router Chain
        # Value contains ip:port and some other info
        self.lanes = {}
        # Route table is a dict whose key is target id in str type and
        # whose value is Lane Chain.
        self.route = {}
        self.config_path = config_path
        self.import_route()
        # Thread(target=self.periodical_gossip, daemon=True).start()

    def periodical_gossip(self):
        while True:
            log.info('Periodical Gossip . . .')
            identifier = uuid.uuid4().hex
            target = Chain(identifier=identifier)
            self.gossip(Chain(identifier=self.data_chain_id), target, 10, [])
            time.sleep(10)

    def import_route(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        route_path = os.path.join(os.path.dirname(self.config_path), config['router']['route_path'])
        if os.path.exists(route_path):
            with open(route_path) as file:
                self.route = yaml.load(file, Loader=yaml.Loader)

    def next_jump(self, target: Chain) -> Chain:
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        if target.identifier not in self.route.keys():
            ttl = config['router']['ttl']
            paths = []
            while True:
                code = self.gossip(Chain(identifier=self.data_chain_id), target, ttl, paths)
                if code is None:
                    return None
                ttl += config['router']['ttl']
        return self.route[target.identifier]

    def gossip(self, source: Chain, target: Chain, ttl, paths: list):
        num_of_neighbours = len(self.lanes)
        if num_of_neighbours <= self.min_router_chain:
            return None
        selecteds = set()
        if num_of_neighbours < self.min_seacher:
            for lane in self.lanes:
                selecteds.add(lane)
        else:
            while True:
                if len(selecteds) == self.min_seacher:
                    break
                selecteds.add(
                    self.lanes[random.randint(0, num_of_neighbours-1)])
        self.transmit_to_others(
            selecteds, source, target, ttl=ttl, paths=paths)
        return DciResCode.OK.value

    def transmit_to_others(self, lanes, source: Chain, target: Chain, ttl, paths: list):
        """Transmit gossip message to each route chain

        Args:
            lanes (list(Lane)): Route chains selected to gossip
            source (Chain): The source data chain who sent gossip
            target (Chain): The target data chain who will been found
            ttl (int): ttl
            paths (list): The list of route path consists of route chain
        """
        for lane in lanes:
            if lane.identifier == paths[-1].identifier:
                continue
            paths.append(Chain(lane.identifier))
            req = RequestGossipQueryPath(
                target=target, source=source, ttl=ttl)
            req.route_chains.extend([path for path in paths])
            tx_json = json.loads(MessageToJson(req))
            log.info(tx_json)
            params = (
                ('tx', '0x' + json.dumps(tx_json).encode('utf-8').hex()),
            )
            log.info('0x' + json.dumps(tx_json).encode('utf-8').hex())
            log.info(f'Connect to http://localhost:{lane.rpc_port}')
            response = requests.get(f'http://localhost:{lane.rpc_port}/broadcast_tx_commit', params=params)
            log.info(response)

    def callback_to_finder(self, source: Chain, target: Chain, paths: list):
        """
        :source is data chain who has been found
        :target is data chain who sent gossip first
        """
        for lane in self.lanes:
            if lane.identifier == paths[-1].identifier:
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
                log.info(f'Connect to http://localhost:{str(lane.port)}')
                response = requests.get(f'http://localhost:{lane.rpc_port}/broadcast_tx_commit', params=params)
                log.info(response)

    def info(self, req: RequestRouterInfo) -> ResponseRouterInfo:
        res = ResponseRouterInfo(code=DciResCode.OK.value,
                                 data=(
                                     'Route Table:\n'+str(self.route)
                                 ).encode('utf-8'),
                                 info='Return route table info!')
        return res

    def transmit(self, req: RequestRouterTransmit) -> ResponseRouterTransmit:
        paths = req.paths
        self.route[req.source.identifier] = paths[-1]
        if req.ttl <= 0:
            return ResponseRouterTransmit(code=DciResCode.OK.value)
        if req.target.identifier == self.data_chain_id:
            self.callback_to_finder(req.target, req.source, paths)
        elif req.target.identifier in self.route:
            self.callback_to_finder(req.target, req.source, paths)
        else:
            self.gossip(req.source, req.target, ttl=req.ttl-1, paths=paths)
        return ResponseRouterTransmit(code=DciResCode.OK.value)

    def callback(self, req: RequestRouterPathCallback) -> ResponseRouterPathCallback:
        paths = req.paths
        self.route[req.source.identifier] = paths[-1]
        for lane in self.lanes:
            if req.target.identifier == lane.identifier:
                return ResponseRouterPathCallback(code=DciResCode.OK.value)
        self.callback_to_finder(req.source, req.target, paths[:-1])
        return ResponseRouterPathCallback(code=DciResCode.OK.value)
