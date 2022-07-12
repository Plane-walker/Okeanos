__all__ = [
    'DockServer',
    'Dock',
]

from concurrent import futures
import grpc
import yaml
from log import log
from interface.dci import dci_pb2_grpc
from dock.netopter import NetworkOptimizer
from dock.cccp import CrossChainCommunicationProtocol
from dock.manager import ChainManager


class DockServer(dci_pb2_grpc.DockServicer):

    def __init__(self, cross_chain_community_protocol, network_optimizer):
        log.info('Init DockServer')
        self.cross_chain_community_protocol = cross_chain_community_protocol
        self.network_optimizer = network_optimizer

    def DeliverTx(self, request, context):
        log.info('Received request for DeliverTx')
        return self.cross_chain_community_protocol.deliver_tx(request)

    def Shard(self, request, context):
        log.info('Received request for Shard')
        return self.network_optimizer.shard(request)

    def Switch(self, request, context):
        log.info('Received request for SwitchIsland')
        return self.network_optimizer.switch(request)


class Dock:
    def __init__(self, config_path):
        self.config_path = config_path
        self.chain_manager = ChainManager(config_path=config_path)
        pool = futures.ThreadPoolExecutor(max_workers=1000)
        cross_chain_community_protocol = CrossChainCommunicationProtocol(config_path, self.chain_manager, pool)
        network_optimizer = NetworkOptimizer(config_path, self.chain_manager, pool)
        self.dock_server = DockServer(cross_chain_community_protocol, network_optimizer)

    def run(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        log.info('Begin to bring up chains')
        for chain_name in config['chain_manager']['chain'].keys():
            self.chain_manager.init_chain(chain_name)
            if not config['chain_manager']['chain'][chain_name]['join']:
                self.chain_manager.add_chain(chain_name)
            else:
                self.chain_manager.join_chain(chain_name)
        log.info('All chains started')
        log.info('Begin to bring up dock service')
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=1000))
        dci_pb2_grpc.add_DockServicer_to_server(self.dock_server, server)
        host = config['dock']['address']['host']
        port = config['dock']['address']['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()
        log.info('Dock service started')
        server.wait_for_termination()
