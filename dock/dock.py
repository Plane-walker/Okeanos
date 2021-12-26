__all__ = [
    'DockServer',
    'Dock',
]

from concurrent import futures
import os
import grpc
import yaml
from interface.dci import dci_pb2_grpc
from dock.router import Router
from dock.netopter import NetworkOptimizer


class DockServer(dci_pb2_grpc.DockServicer):

    def __init__(self, router):
        self.router = router

    def RouterInfo(self, request, context):
        return self.router.info(request)

    def RouterTransmit(self, request, context):
        return self.router.transmit(request)

    def RouterPathCallback(self, request, context):
        return self.router.callback(request)


class Dock:
    def __init__(self, config_path=None):
        router = Router()
        network_optimizer = NetworkOptimizer(0, 0)
        self.dock_server = DockServer(router)
        if config_path is None:
            current_path = os.path.dirname(__file__)
            config_path = os.path.join(current_path, 'default_config.yaml')
        with open(config_path) as file:
            self.config = yaml.load(file, Loader=yaml.Loader)

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(self.dock_server, server)
        host = self.config['dock']['address']['host']
        port = self.config['dock']['address']['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()
        server.wait_for_termination()
