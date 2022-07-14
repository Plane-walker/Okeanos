import base64
import unittest
from concurrent import futures
import grpc
from interface.dci import dci_pb2_grpc
import os
from dock import Dock
import requests
import json
import yaml
import time


class TestGraphData(unittest.TestCase):
    def test_graph_data(self):
        current_path = os.path.dirname(__file__)
        dock_config_path = os.path.join(current_path, 'config/dock.yaml')
        dock = Dock(dock_config_path)
        with open(dock.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        dock_manager_path = config['chain_manager']['base_path']
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

        dock_1_config_path = os.path.join(current_path, 'config/dock1.yaml')
        with open(dock_1_config_path) as file:
            config_1 = yaml.load(file, Loader=yaml.Loader)
        dock_1 = Dock(dock_1_config_path)
        for chain_name in config_1['chain_manager']['chain'].keys():
            dock_1.chain_manager.init_chain(chain_name)
            if not config_1['chain_manager']['chain'][chain_name]['join']:
                dock_1.chain_manager.add_chain(chain_name)
            else:
                dock_1.chain_manager.join_chain(chain_name)
        server_1 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(dock_1.dock_server, server_1)
        host_1 = config_1['dock']['address']['host']
        port_1 = config_1['dock']['address']['port']
        server_1.add_insecure_port(f'{host_1}:{port_1}')
        server_1.start()
        # accept the source and the target
        dock_island_genesis_path = os.path.join(dock_manager_path, 'island_0/config/genesis.json')
        with open(dock_island_genesis_path) as file:
            self.source = yaml.load(file, Loader=yaml.Loader)
        with open(os.path.join(dock_manager_path, 'island_0/config/priv_validator_key.json')) as file:
            priv_validator_key = yaml.load(file, Loader=yaml.Loader)
        source_node_id = priv_validator_key['address']
        dock_1_manager_path = config_1['chain_manager']['base_path']
        dock_1_island_genesis_path = os.path.join(dock_1_manager_path, 'island_1/config/genesis.json')
        with open(dock_1_island_genesis_path) as file:
            self.target = yaml.load(file, Loader=yaml.Loader)
        with open(os.path.join(dock_manager_path, 'island_1/config/priv_validator_key.json')) as file:
            priv_validator_key = yaml.load(file, Loader=yaml.Loader)
        target_node_id = priv_validator_key['address']
        message = {
            "header": {
                "type": "write",
                "timestamp": str(time.time())
            },
            "body": {
                "key": "test_key_source",
                "value": 10
            }
        }
        params = (
            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        requests.get(
            f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/broadcast_tx_commit", params=params)

        cross_timestamp = str(time.time())
        message = {
            "header": {
                "type": "cross_move_source",
                "cross": {
                    "ttl": -1,
                    "paths": [],
                    "source_chain_id": self.source['chain_id'],
                    "source_node_id": source_node_id,
                    "source_info": source_node_id,
                    "target_chain_id": self.target['chain_id'],
                    "target_node_id": target_node_id,
                    "target_info": target_node_id,
                },
                "timestamp": cross_timestamp
            },
            "body": {
                "source_key": "test_key_source",
                "target_key": "test_key_target",
                "amount": 3
            }
        }

        params = (
            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        requests.get(f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/broadcast_tx_commit", params=params)
        message = {
            "header": {
                "type": "graph",
                "timestamp": str(time.time())
            },
            "body": {}
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        response = requests.get(f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)
        result = json.loads(base64.b64decode(json.loads(response.text)['result']['response']['value'].encode('utf-8')).decode('utf-8'))
        self.assertEqual(result[0]['source_node_id'], source_node_id)
        self.assertEqual(result[0]['target_node_id'], target_node_id)
        self.assertEqual(result[0]['weight'][0], cross_timestamp)
        for chain in dock.chain_manager.select_chain(lambda single: True):
            dock.chain_manager.delete_chain(chain.chain_id)
        for chain in dock_1.chain_manager.select_chain(lambda single: True):
            dock_1.chain_manager.delete_chain(chain.chain_id)


if __name__ == '__main__':
    unittest.main()
