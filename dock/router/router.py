__all__ = [
    'Router',
    'Chain',
]


import random
import grpc
import os
import yaml
from interface.dci.dci_pb2 import Chain as DciChain
from interface.dci.dci_pb2 import (
    RequestRouterInfo,
    ResponseRouterInfo,
    RequestRouterPathCallback,
    ResponseRouterPathCallback,
    RequestRouterTransmit,
    ResponseRouterTransmit,
)
from interface.bci.bci_pb2_grpc import LaneStub
from interface.bci.bci_pb2 import Chain as BciChain
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


class Chain:

    def __init__(self, chain):
        if isinstance(chain, int):
            self.identifier = chain
        else:
            self.identifier = chain.identifier

    def dci(self) -> DciChain:
        return DciChain(identifier=self.identifier)

    def bci(self) -> BciChain:
        return BciChain(identifier=self.identifier)


class Router:

    def __init__(self, config_path) -> None:
        self.node_id = 0
        self.data_chain_id = 0

        # Key is the id of Router Chain
        # Value contains ip:port and some other info
        self.lanes = {}

        # Route table is a dict whose key is target id in uint type and
        # whose value is Lane Chain in Chain type.
        self.route = {}
        with open(config_path, encoding='utf-8') as file:
            config = yaml.load(file, Loader=yaml.Loader)
            self.configure(config['router'])

    def configure(self, config: dict, config_key=None):
        if not isinstance(config, dict):
            return
        if config_key is None:
            keys = ('ttl', 'min_router_chain', 'min_search')
            for key in keys:
                if key not in config:
                    raise KeyError
                self.__setattr__(key, config[key])
        else:
            if config_key not in config:
                raise KeyError
            self.__setattr__(config_key, config[config_key])

    def next_node(self, target: Chain) -> Chain:
        ttl = self.ttl
        paths = []
        id = target.identifier
        while True:
            if id in self.route:
                break
            code = self.gossip(Chain(self.data_chain_id), target, ttl, paths)
            if code is None:
                return None
            ttl += self.ttl
            # TODO Sleep some time
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
                target=target.bci(), source=source.bci(), ttl=ttl)
            req.route_chains.extend([path.bci() for path in paths])
            with grpc.insecure_channel('localhost:'+str(lane.port)) as channel:
                log.info('Connect to ', channel)
                stub = LaneStub(channel)
                res = stub.GossipQueryPath(req)

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
                    target=target.bci(), source=source.bci())
                req.route_chains.extend([path.bci() for path in paths])
                with grpc.insecure_channel('localhost:'+str(lane.port)) as channel:
                    log.info('Connect to ', channel)
                    stub = LaneStub(channel)
                    res = stub.GossipCallBack(req)

    def info(self, req: RequestRouterInfo) -> ResponseRouterInfo:
        res = ResponseRouterInfo(code=DciResCode.OK.value,
                                 data=(
                                     'Route Table:\n'+str(self.route)
                                 ).encode('utf-8'),
                                 info='Return route table info!')
        return res

    def transmit(self, req: RequestRouterTransmit) -> ResponseRouterTransmit:
        paths = []
        for path in req.paths:
            paths.append(Chain(path))
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
        paths = []
        for path in req.paths:
            paths.append(Chain(path))
        self.route[req.source.identifier] = paths[-1]
        for lane in self.lanes:
            if req.target.identifier == lane.identifier:
                return ResponseRouterPathCallback(code=DciResCode.OK.value)
        self.callback_to_finder(req.source, req.target, paths[:-1])
        return ResponseRouterPathCallback(code=DciResCode.OK.value)
