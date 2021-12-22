__all__ = [
    "Router",
]


import random
import grpc
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


MIN_LANES = 3
MIN_SEACHER = 3
SUCCESS_CODE = 0
DEFAULT_TTL = 10


class Chain:
    
    def __init__(self, chain: DciChain):
        self.identifier = chain.identifier
        
    def __init__(self, chain:BciChain):
        self.identifier = chain.identifier
        
    def __init__(self, identifier: int):
        self.identifier = identifier
    
    def dci(self) -> DciChain:
        return DciChain(identifier=self.identifier)
    
    def bci(self) -> BciChain:
        return BciChain(identifier=self.identifier)


class Router:

    def __init__(self) -> None:
        self.node_id = 0
        self.lanes = set()
        
        # Route table is a dict whose key is target id in uint type and whose value
        # is Lane Chain in Chain type.
        self.route = dict()
        self.rid = 0
        
        return None

    def next_node(self, target: Chain) -> Chain:
        ttl = DEFAULT_TTL
        paths = []
        id = target.identifier
        while True:
            if id in self.route:
                break
            code = self.gossip(Chain(identifier=self.rid), target, ttl, paths)
            if code is None:
                return None
            ttl += DEFAULT_TTL
            # TODO Sleep some time
        return self.route[target.identifier]

    def gossip(self, source: Chain, target: Chain, ttl, paths: list):
        num_of_neighbours = len(self.lanes)
        if num_of_neighbours <= MIN_LANES:
            return None
        selecteds = set()
        if num_of_neighbours < MIN_SEACHER:
            for lane in self.lanes:
                selecteds.add(lane)
        else:
            while True:
                if len(selecteds) == MIN_SEACHER:
                    break
                selecteds.add(self.lanes[random.randint(0, num_of_neighbours-1)])
        self.transmit_to_others(selecteds, source, target, ttl=ttl, paths=paths)
        return SUCCESS_CODE

    def transmit_to_others(self, lanes, source: Chain, target: Chain, ttl, paths: list):
        for lane in lanes:
            if lane.identifier == paths[-1].identifier:
                continue
            paths.append(Chain(identifier=lane.identifier))
            req = RequestGossipQueryPath(target=target.bci(), source=source.bci(), ttl=ttl)
            req.route_chains.extend([path.bci() for path in paths])
            with grpc.insecure_channel('localhost:'+str(lane.port)) as channel:
                stub = LaneStub(channel)
                res = stub.GossipQueryPath(req)

    def callback_to_finder(self, source: Chain, target: Chain, paths: list):
        """
        :source is who has been found
        :target is who sent gossip first
        """
        for lane in self.lanes:
            if lane.identifier == paths[-1].identifier:
                # The source in RequestGossipCallBack is who has been found and then
                # sends callback. And the target in RequestGossipCallBack is who sent
                # gossip first and waiting now.
                req = RequestGossipCallBack(target=target.bci(), source=source.bci())
                req.route_chains.extend([path.bci() for path in paths])
                with grpc.insecure_channel('localhost:'+str(lane.port)) as channel:
                    stub = LaneStub(channel)
                    res = stub.GossipCallBack(req)

    def info(self, req: RequestRouterInfo) -> ResponseRouterInfo:
        res = ResponseRouterInfo(code=SUCCESS_CODE,
                                 data=('Route Table:\n'+str(self.route)).encode('utf-8'),
                                 info="Return route table info!")
        return res

    def transmit(self, req: RequestRouterTransmit) -> ResponseRouterTransmit:
        paths = []
        for path in req.paths:
            paths.append(Chain(path))
        self.route[req.source.identifier] = paths[-1]
        if req.ttl <= 0:
            return ResponseRouterTransmit(code=SUCCESS_CODE)
        if req.target.identifier in self.route:
            self.callback_to_finder(req.target, req.source, paths)
        else:
            self.gossip(req.source, req.target, ttl=req.ttl-1, paths=paths)
        return ResponseRouterTransmit(code=SUCCESS_CODE)

    def callback(self, req: RequestRouterPathCallback) -> ResponseRouterPathCallback:
        paths = []
        for path in req.paths:
            paths.append(Chain(path))
        self.route[req.source.identifier] = paths[-1]
        for lane in self.lanes:
            if req.target.identifier == lane.identifier:
                return RequestRouterPathCallback(code=SUCCESS_CODE)
        self.callback_to_finder(req.source, req.target, paths[:-1])
        return RequestRouterPathCallback(code=SUCCESS_CODE)
