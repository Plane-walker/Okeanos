__all__ = [
    "Router",
]

from dock.interface.dci_pb2 import (
    Chain,
    RequestRouterInfo,
    ResponseRouterInfo,
    RequestRouterPathCallback,
    ResponseRouterPathCallback,
    RequestRouterTransmit,
    ResponseRouterTransmit,
)


class Router:
    
    def __init__(self) -> None:
        self.lanes = set()
        self.paths = dict()
        return None
    
    def next_node(self, target: Chain) -> Chain:
        if target.identifier in self.paths:
            return self.paths[target.identifier]
        else:
            return self.gossip(target)
    
    def gossip(self, target: Chain) -> Chain:
        # TODO Gossip
        return None
