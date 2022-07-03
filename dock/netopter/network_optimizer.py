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
        self.chain_manager = chain_manager
        self.config_path = config_path
        self.pool = pool
        self.model = GraphSAGEModel(config_path=config_path, chain_manager=chain_manager)

    def update_model(self):
        graph_data = GraphData(self.config_path)
        graph_data.import_data_from_file('cora')
        self.model.train(graph_data)
        self.model.save_model()

    def optimize_async(self, request):
        def optimize():
            try:
                graph_data = GraphData(self.config_path)
                graph_data.import_data_from_str(request.graph_state)
                new_chain_id = self.model.predict(graph_data)[0]
                log.info(f'New chain id is {new_chain_id}')
                if new_chain_id == self.chain_manager.get_island()[0].chain_id:
                    return
                with open(self.config_path) as file:
                    config = yaml.load(file, Loader=yaml.Loader)
                message = {
                    "header": {
                        "type": "join",
                        "cross": {
                            "ttl": -1,
                            "paths": [],
                            "source_chain_id": self.chain_manager.get_island()[0].chain_id,
                            "target_chain_id": new_chain_id
                        },
                        "timestamp": str(time.time())
                    },
                    "body": {}
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
                    message = {
                        "header": {
                            "type": "delete",
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
                    for chain in self.chain_manager.select_chain(lambda input_chain: True):
                        self.chain_manager.delete_chain(chain.chain_id)
                    result = json.loads(base64.b64decode(json.loads(response.text)['result']['response']['value'].encode('utf-8')).decode('utf-8'))
                    for chain_name in config['chain_manager']['chain'].keys():
                        config['chain_manager']['chain'][chain_name]['join'] = True
                        if config['chain_manager']['chain'][chain_name]['type'] == 'island':
                            island_address = result['island'].pop(0)
                            host, port = island_address.split(':')
                            config['chain_manager']['chain'][chain_name]['persistent_peers'] = [{'host': host, 'port': port}]
                        elif config['chain_manager']['chain'][chain_name]['type'] == 'lane':
                            lane_address = result['lane'].pop(0)
                            host, port = lane_address.split(':')
                            config['chain_manager']['chain'][chain_name]['persistent_peers'] = [{'host': host, 'port': port}]
                        with open(self.config_path, 'w') as file:
                            yaml.dump(config, file, default_flow_style=False, sort_keys=False)
                        self.chain_manager.init_chain(chain_name)
                        self.chain_manager.join_chain(chain_name)
            except Exception as exception:
                log.error(repr(exception))
        self.pool.submit(optimize)

    def shard(self, request):
        self.optimize_async(request)
        return dci_pb2.ResponseShard(code=200, info='ok')
