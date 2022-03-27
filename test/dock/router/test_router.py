import base64
from datetime import datetime
import shutil
import unittest
from concurrent import futures
import grpc
from interface.dci import dci_pb2_grpc
import os
from dock import Dock
import requests
import json
import yaml
import subprocess
import time
import datetime


class TestRouter(unittest.TestCase):
    def test_router(self):
        current_path = os.path.dirname(__file__)
        dock_config_path = os.path.join(current_path, 'config/dock.yaml')
        self.dock = Dock(dock_config_path)
        with open(self.dock.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        dock_manager_path = config['chain_manager']['base_path']
        for chain_name in config['chain_manager']['chain'].keys():
            self.dock.chain_manager.init_chain(chain_name)
            if not config['chain_manager']['chain'][chain_name]['join']:
                self.dock.chain_manager.add_chain(chain_name)
            else:
                self.dock.chain_manager.join_chain(chain_name)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(self.dock.dock_server, server)
        host = config['dock']['address']['host']
        port = config['dock']['address']['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()

        dock_1_config_path = os.path.join(current_path, 'config/dock1.yaml')
        with open(dock_1_config_path) as file:
            config_1 = yaml.load(file, Loader=yaml.Loader)
        self.dock_1 = Dock(dock_1_config_path)
        for chain_name in config_1['chain_manager']['chain'].keys():
            self.dock_1.chain_manager.init_chain(chain_name)
            if not config_1['chain_manager']['chain'][chain_name]['join']:
                self.dock_1.chain_manager.add_chain(chain_name)
            else:
                self.dock_1.chain_manager.join_chain(chain_name)
        server_1 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(self.dock_1.dock_server, server_1)
        host_1 = config_1['dock']['address']['host']
        port_1 = config_1['dock']['address']['port']
        server_1.add_insecure_port(f'{host_1}:{port_1}')
        server_1.start()
        # accept the source and the target
        dock_island_genesis_path = os.path.join(dock_manager_path, 'island_0/config/genesis.json')
        with open(dock_island_genesis_path) as file:
            self.source = yaml.load(file, Loader=yaml.Loader)
        dock_1_manager_path = config_1['chain_manager']['base_path']
        dock_1_island_genesis_path = os.path.join(dock_1_manager_path, 'island_1/config/genesis.json')
        with open(dock_1_island_genesis_path) as file:
            self.target = yaml.load(file, Loader=yaml.Loader)

        # deliver_tx
        message = {
            "header": {
                "type": "cross_write",
                "ttl": -1,
                "paths": [],
                "source_chain_id": self.source['chain_id'],
                "target_chain_id": self.target['chain_id'],
                "auth": {
                    "app_id": "0"
                },
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
        requests.get(
            f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/broadcast_tx_commit", params=params)

        # query_txs
        message = {
            "header": {
                "type": "read",
                "ttl": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": "0"
                },
                "timestamp": str(time.time())
            },
            "body": {
                "key": "test_key"
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )

        start_time = datetime.datetime.now()
        timeout = 30
        while True:
            response = requests.get(
                f"http://localhost:{config_1['chain_manager']['chain']['island_1']['rpc_port']}/abci_query", params=params)
            if json.loads(response.text)['result']['response']['value'] == 'test_value':
                break
            if (datetime.datetime.now() - start_time).seconds > timeout:
                break
            time.sleep(1)

        self.assertEqual(json.loads(response.text)['result']['response']['value'], base64.b64encode('"test_value"'.encode('utf-8')).decode('utf-8'))
        message = {
            "header": {
                "type": "cross_read",
                "ttl": -1,
                "paths": [],
                "source_chain_id": self.source['chain_id'],
                "target_chain_id": self.target['chain_id'],
                "auth": {
                    "app_id": "0"
                },
                "timestamp": str(time.time())
            },
            "body": {
                "key": "test_key",
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        requests.get(f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)

        message = {
            "header": {
                "type": "read",
                "ttl": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": "0"
                },
                "timestamp": str(time.time())
            },
            "body": {
                "key": "response_for_query_test_key",
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )

        start_time = datetime.datetime.now()
        while True:
            response = requests.get(
                f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)
            if json.loads(response.text)['result']['response']['value'] == 'test_value':
                break
            if (datetime.datetime.now() - start_time).seconds > timeout:
                break
            time.sleep(1)

        self.assertEqual(json.loads(response.text)['result']['response']['value'], base64.b64encode('"test_value"'.encode('utf-8')).decode('utf-8'))

        # delete chains
        for chain in self.dock.chain_manager.select_chain(lambda single: True):
            self.dock.chain_manager.delete_chain(chain.chain_id)
        for chain in self.dock_1.chain_manager.select_chain(lambda single: True):
            self.dock_1.chain_manager.delete_chain(chain.chain_id)


if __name__ == '__main__':
    unittest.main()
