from time import sleep
import unittest
from concurrent import futures
import grpc
from interface.dci import dci_pb2_grpc
import os
from dock import Dock
import requests
import json
import yaml


class TestRouter(unittest.TestCase):
    def test_router(self):
        current_path = os.path.dirname(__file__)
        dock_config_path = os.path.join(current_path, 'config/dock.yaml')
        self.dock = Dock(dock_config_path)
        with open(self.dock.config_path) as file:
            self.config = yaml.load(file, Loader=yaml.Loader)
        for chain_name in self.config['chain_manager']['chain'].keys():
            self.dock.chain_manager.init_chain(chain_name)
            if not self.config['chain_manager']['chain'][chain_name]['join']:
                self.dock.chain_manager.add_chain(chain_name)
            else:
                self.dock.chain_manager.join_chain(chain_name)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(self.dock.dock_server, server)
        host = self.config['dock']['address']['host']
        port = self.config['dock']['address']['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()

        params = (
            ('tx', '0x' + json.dumps({'info': ''}).encode('utf-8').hex()),
        )
        response = requests.get(f"http://localhost:{self.config['chain_manager']['chain']['lane_0']['rpc_port']}/broadcast_tx_commit", params=params)
        self.assertEqual(json.loads(response.text)['result']['deliver_tx']['code'], 0)

        lanes = self.dock.chain_manager.get_lane()
        param = {
            'source': 'FarawaySource',
            'target': 'FarAwayTarget',
            'paths': [lanes[0].chain_id],
            'ttl': 2
        }
        params = (
            ('tx', '0x' + json.dumps(param).encode('utf-8').hex()),
        )
        response = requests.get(f"http://localhost:{self.config['chain_manager']['chain']['lane_0']['rpc_port']}/broadcast_tx_commit", params=params)
        self.assertEqual(json.loads(response.text)['result']['deliver_tx']['code'], 0)

        lanes = self.dock.chain_manager.get_lane()
        island = self.dock.chain_manager.get_island()[0]
        param = {
            'source': 'FarAwaySource',
            'target': island.chain_id,
            'paths': [lanes[0].chain_id]
        }
        params = (
            ('tx', '0x' + json.dumps(param).encode('utf-8').hex()),
        )
        response = requests.get(f"http://localhost:{self.config['chain_manager']['chain']['lane_0']['rpc_port']}/broadcast_tx_commit", params=params)
        self.assertEqual(json.loads(response.text)['result']['deliver_tx']['code'], 0)
        router = self.dock.dock_server.router
        self.assertIn('FarAwaySource', router.route)


if __name__ == '__main__':
    unittest.main()
