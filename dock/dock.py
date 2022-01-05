__all__ = [
    'DockServer',
    'Dock',
]

from concurrent import futures
import grpc
import yaml
from log import log
from interface.dci import dci_pb2_grpc
from dock.router import Router
from dock.netopter import NetworkOptimizer
from dock.cccp import CrossChainCommunicationProtocol
from dock.manager import ChainManager


class DockServer(dci_pb2_grpc.DockServicer):

    def __init__(self, router, cccp, network_optimizer):
        log.info('Init DockServer')
        self.router = router
        self.cccp = cccp
        self.network_optimizer = network_optimizer

    def PackageTx(self, request, context):
        return self.cccp.deliver_tx(request)

    def RouterInfo(self, request, context):
        log.info('Request from %s', context.peer())
        return self.router.info(request)

    def RouterTransmit(self, request, context):
        log.info('Request from %s', context.peer())
        return self.router.transmit(request)

    def RouterPathCallback(self, request, context):
        log.info('Request from %s', context.peer())
        return self.router.callback(request)


class Dock:
    def __init__(self, config_path):
        log.info('Init Dock . . .')
        router = Router(config_path=config_path)
        cccp = CrossChainCommunicationProtocol(router)
        network_optimizer = NetworkOptimizer(0, 0, config_path=config_path)
        self.dock_server = DockServer(router, cccp, network_optimizer)
        self.chain_manager = ChainManager(config_path=config_path)
        with open(config_path) as file:
            self.config = yaml.load(file, Loader=yaml.Loader)

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(self.dock_server, server)
        host = self.config['dock']['address']['host']
        port = self.config['dock']['address']['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()
        self.chain_manager.create_chain('island')
        for index in range(self.config['chain_manager']['lane_number']):
            self.chain_manager.create_chain('lane', index)
        server.wait_for_termination()
