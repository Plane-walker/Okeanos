__all__ = [
    "Router",
]

import asyncio
import queue
import threading
import requests
from google.protobuf import json_format
from requests.models import codes
from dock.interface.dci_pb2 import (
    Chain,
    RequestRouterInfo,
    ResponseRouterInfo,
    RequestRouterPathCallback,
    ResponseRouterPathCallback,
    RequestRouterTransmit,
    ResponseRouterTransmit,
)
from dock.interface.bci_pb2 import (
    RequestGossipQueryPath,
    ResponseGossipQueryPath,
    RequestGossipCallBack,
    ResponseGossipCallBack,
)


class Router:

    def __init__(self) -> None:
        self.lanes = set()
        self.paths = dict()
        self.queue = queue.Queue()
        return None

    def next_node(self, target: Chain) -> Chain:
        if target.identifier in self.paths:
            return self.paths[target.identifier]
        else:
            return self.gossip(target)

    def gossip(self, target: Chain) -> Chain:
        # TODO Gossip
        return None

    async def run(self):
        pass

    async def produce(self):
        pass

    async def consume(self):
        pass


HEADERS = {'Content-Type': 'application/json'}
SUCCESS_CODE = 0


class BciSender:

    def __init__(self, queue: queue.Queue):
        self.queue = queue

    def transmit(self, url, req: RequestGossipQueryPath) -> ResponseGossipQueryPath:
        res = requests.post(url=url, headers=HEADERS, data=json_format.MessageToJson(req))
        return res

    def callback(self, url, req: RequestGossipCallBack) -> ResponseGossipCallBack:
        res = requests.post(url=url, headers=HEADERS, data=json_format.MessageToJson(req))
        return res

class DciServer:

    def __init__(self, queue: queue.Queue):
        self.queue = queue

    def transmit(self, req: RequestRouterTransmit) -> ResponseRouterTransmit:
        self.queue.put(req)
        return ResponseRouterTransmit(code=SUCCESS_CODE)

    def callback(self, req: RequestRouterPathCallback) -> ResponseRouterPathCallback:
        self.queue.put(req)
        return ResponseRouterPathCallback(code=SUCCESS_CODE)
