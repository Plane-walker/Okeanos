from dock import Dock
import os
import requests
import json
from concurrent import futures
import grpc
import base64
import yaml
import time
from interface.dci import dci_pb2_grpc
import unittest


class TestCCCP(unittest.TestCase):
    def test_island_deliver_tx(self):
        current_path = os.path.dirname(__file__)
        dock_config_path = os.path.join(current_path, 'config/dock.yaml')
        dock = Dock(dock_config_path)
        with open(dock.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        for chain_name in config['chain_manager']['chain'].keys():
            dock.chain_manager.init_chain(chain_name)
            if not config['chain_manager']['chain'][chain_name]['join']:
                dock.chain_manager.add_chain(chain_name)
            else:
                dock.chain_manager.join_chain(chain_name)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(dock.dock_server, server)
        host = config['dock']['address']['host']
        port = config['dock']['address']['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()
        message = {
            "header": {
                "type": "write",
                "timestamp": str(time.time())
            },
            "body": {
                "key": "test_key",
                "value": "test_value"
            }
        }
        params = (
            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        requests.get(f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/broadcast_tx_commit", params=params)
        message = {
            "header": {
                "type": "read",
                "timestamp": str(time.time())
            },
            "body": {
                "key": "test_key"
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        response = requests.get(f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)
        self.assertEqual(json.loads(response.text)['result']['response']['value'], base64.b64encode('"test_value"'.encode('utf-8')).decode('utf-8'))
        for chain in dock.chain_manager.select_chain(lambda single: True):
            dock.chain_manager.delete_chain(chain.chain_id)


if __name__ == '__main__':
    unittest.main()
