__all__ = [
    'NetworkOptimizer'
]

from log import log
import yaml
import json
import datetime
import base64
import time
import requests
from .node_classification import GraphSAGEModel
from .graph_data import GraphData
from interface.dci import dci_pb2


class NetworkOptimizer:
    def __init__(self, config_path, chain_manager, pool):
        self.graph_data = GraphData(config_path)
        self.chain_manager = chain_manager
        self.config_path = config_path
        self.pool = pool
        self.model = GraphSAGEModel(config_path=config_path)

    def update_model(self):
        self.model.train(self.graph_data)
        self.model.save_model()

    def join_async(self):
        def join():
            self.graph_data.update_neighbors_data()
            new_chain_id = self.model.predict(self.graph_data)
            log.info(f'New chain id is {new_chain_id}')
            with open(self.config_path) as file:
                config = yaml.load(file, Loader=yaml.Loader)
            message = {
                "header": {
                    "type": "join",
                    "ttl": -1,
                    "paths": [],
                    "source_chain_id": self.chain_manager.get_island()[0].chain_id,
                    "target_chain_id": new_chain_id,
                    "auth": {
                        "app_id": config['app']['app_id']
                    },
                    "timestamp": str(time.time())
                },
                "body": {}
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
                        "app_id": config['app']['app_id']
                    },
                    "timestamp": str(time.time())
                },
                "body": {
                    "key": f"response_for_query_join_{new_chain_id}"
                }
            }
            params = (
                ('data', '0x' + json.dumps(message).encode('utf-8').hex()),
            )
            start_time = datetime.datetime.now()
            timeout = 30
            while True:
                response = requests.get(
                    f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/abci_query", params=params)
                if json.loads(response.text)['result']['response']['code'] == 0 or (datetime.datetime.now() - start_time).seconds > timeout:
                    break
                time.sleep(1)
            if json.loads(response.text)['result']['response']['code'] == 0:
                for chain_id in self.chain_manager.select_chain(lambda chain: True):
                    self.chain_manager.delete_chain(chain_id)
                result = json.loads(base64.b64decode(json.loads(response.text)['result']['response']['value'].encode('utf-8')).decode('utf-8'))
                for chain_name in config['chain_manager']['chain'].keys():
                    config['chain_manager']['chain'][chain_name]['join'] = True
                    if config['chain_manager']['chain'][chain_name]['type'] == 'island':
                        config['chain_manager']['chain'][chain_name]['persistent_peers'] = result['island'].pop(0)
                    elif config['chain_manager']['chain'][chain_name]['type'] == 'lane':
                        config['chain_manager']['chain'][chain_name]['persistent_peers'] = result['lane'].pop(0)
                    self.chain_manager.init_chain(chain_name)
                    self.chain_manager.add_chain(chain_name)
                with open(self.config_path, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False, sort_keys=False)
            message = {
                "header": {
                    "type": "delete",
                    "ttl": -1,
                    "paths": [],
                    "source_chain_id": "",
                    "target_chain_id": "",
                    "auth": {
                        "app_id": config['app']['app_id']
                    },
                    "timestamp": str(time.time())
                },
                "body": {
                    "key": f"response_for_query_join_{new_chain_id}"
                }
            }
            params = (
                ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
            )
            requests.get(f"http://localhost:{config['chain_manager']['chain']['island_0']['rpc_port']}/broadcast_tx_commit", params=params)
        self.pool.submit(join)

    def switch_island(self, request):
        self.join_async()
        return dci_pb2.ResponseSwitchIsland(code=200, info='ok')
