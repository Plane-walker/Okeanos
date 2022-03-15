import base64
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


class TestRouter(unittest.TestCase):
    def test_router(self):
        current_path = os.path.dirname(__file__)
        dock_config_path = os.path.join(current_path, 'config/dock.yaml')
        self.dock = Dock(dock_config_path)
        with open(self.dock.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
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

        # create the needed direction: genesis and dock1
        mkdir_dir = f"if [ ! -d {config['chain_manager']['base_path']}/dock1 ]; then \n" \
                    f"    mkdir {config['chain_manager']['base_path']}/dock1 \n" \
                    f"fi; \n" \
                    f"if [ ! -d {config['chain_manager']['base_path']}/dock1/genesis ]; then \n" \
                    f"    mkdir {config['chain_manager']['base_path']}/dock1/genesis \n" \
                    f"    mkdir {config['chain_manager']['base_path']}/dock1/genesis/island_0 \n" \
                    f"    mkdir {config['chain_manager']['base_path']}/dock1/genesis/lane_0 \n" \
                    f"    mkdir {config['chain_manager']['base_path']}/dock1/genesis/lane_1 \n" \
                    f"    mkdir {config['chain_manager']['base_path']}/dock1/genesis/lane_2 \n" \
                    f"fi; \n"
        subprocess.run(mkdir_dir, shell=True, stdout=subprocess.PIPE)

        # copy genesis and modify correct dock.yaml
        dock_manager_path = config['chain_manager']['base_path']
        dock_lane_genesis_file = os.path.join(dock_manager_path, 'lane_0/config/genesis.json')
        output = subprocess.getstatusoutput(f"tendermint show-node-id --home {config['chain_manager']['base_path']}/lane_0")
        node_id = output[1]
        dock_1_config_path = os.path.join(current_path, 'config/dock1.yaml')
        with open(dock_1_config_path) as file:
            config_1 = yaml.load(file, Loader=yaml.Loader)
        shutil.copy(dock_lane_genesis_file, f"{config_1['chain_manager']['base_path']}/{config_1['chain_manager']['chain']['lane_0']['genesis_path']}/genesis.json")
        config_1['chain_manager']['chain']['lane_0']['join'] = True
        config_1['chain_manager']['chain']['lane_0']['persistent_peers'] = [f'{node_id}@localhost:2667']
        with open(dock_1_config_path, 'w') as file:
            yaml.dump(config_1, file, default_flow_style=False, sort_keys=False)

        # Start second Dock
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
        dock_1_island_genesis_path = os.path.join(dock_1_manager_path, 'island_0/config/genesis.json')
        with open(dock_1_island_genesis_path) as file:
            self.target = yaml.load(file, Loader=yaml.Loader)

        # deliver_tx
        message = {
            "header": {
                "type": "cross",
                "ttl": -1,
                "index": -1,
                "paths": [],
                "source_chain_id": self.source['chain_id'],
                "target_chain_id": self.target['chain_id'],
                "auth": {
                    "app_id": "0"
                }
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

        time.sleep(10)

        # query_txs
        message = {
            "header": {
                "type": "normal",
                "ttl": -1,
                "index": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": "0"
                }
            },
            "body": {
                "query": "test_key",
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        response = requests.get(
            f"http://localhost:{config_1['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)

        self.assertEqual(json.loads(response.text)['result']['response']['value'], base64.b64encode('"test_value"'.encode('utf-8')).decode('utf-8'))
        message = {
            "header": {
                "type": "query",
                "ttl": -1,
                "index": -1,
                "paths": [],
                "source_chain_id": self.source['chain_id'],
                "target_chain_id": self.target['chain_id'],
                "auth": {
                    "app_id": "0"
                }
            },
            "body": {
                "query": "test_key",
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        response = requests.get(
            f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)

        time.sleep(10)

        message = {
            "header": {
                "type": "normal",
                "ttl": -1,
                "index": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": "0"
                }
            },
            "body": {
                "query": "response_for_query_test_key",
            }
        }
        params = (
            ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        response = requests.get(
            f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)

        self.assertEqual(json.loads(response.text)['result']['response']['value'], base64.b64encode('"test_value"'.encode('utf-8')).decode('utf-8'))

        # delete chains
        for chain in self.dock.chain_manager.select_chain(lambda single: True):
            self.dock.chain_manager.delete_chain(chain.chain_id)
        for chain in self.dock_1.chain_manager.select_chain(lambda single: True):
            self.dock_1.chain_manager.delete_chain(chain.chain_id)


if __name__ == '__main__':
    unittest.main()
