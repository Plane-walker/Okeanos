__all__ = [
    'ChainManager'
]

import os
import subprocess
import signal
import json
import requests
import yaml
import socket
import time
import datetime
from log import log


class BaseChain:
    def __init__(self, chain_type, chain_id, chain_pid, service_pid, chain_name, rpc_port):
        self.chain_type = chain_type
        self.chain_id = chain_id
        self.chain_pid = chain_pid
        self.service_pid = service_pid
        self.chain_name = chain_name
        self.rpc_port = rpc_port


class ChainManager:
    def __init__(self, config_path):
        self._config_path = config_path
        self._chains = {}

    def select_chain(self, condition):
        return [chain for chain in self._chains.values() if condition(chain)]

    def get_lane(self, chain_id=None):
        if chain_id is None:
            return self.select_chain(lambda chain: chain.chain_type == 'lane')
        elif chain_id in self._chains:
            return self._chains[chain_id]
        return None

    def get_island(self, chain_id=None):
        if chain_id is None:
            return self.select_chain(lambda chain: chain.chain_type == 'island')
        elif chain_id in self._chains:
            return self._chains[chain_id]
        return None

    def init_chain(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        init_chain = f"tendermint init --home {config['chain_manager']['base_path']}/{chain_name};" \
                     f"sed -i " \
                     f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['chain_manager']['chain'][chain_name]['abci_port']}\"#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;" \
                     f"sed -i " \
                     f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://0.0.0.0:{config['chain_manager']['chain'][chain_name]['rpc_port']}\"#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;" \
                     f"sed -i " \
                     f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['chain_manager']['chain'][chain_name]['p2p_port']}\"#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;" \
                     f"sed -i " \
                     f"'s#create_empty_blocks = true#create_empty_blocks = false#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;" \
                     f"sed -i " \
                     f"'s#addr_book_strict = true#addr_book_strict = false#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;" \
                     f"sed -i " \
                     f"'s#max_subscription_clients = 100#max_subscription_clients = 8000#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;" \
                     f"sed -i " \
                     f"'s#max_subscriptions_per_client = 5#max_subscriptions_per_client = 400#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml;"
        subprocess.run(init_chain, shell=True, stdout=subprocess.PIPE)

    def _start_chain_core(self, chain_name, join=False):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        if not join:
            start_chain = f"tendermint start --home {config['chain_manager']['base_path']}/{chain_name} " \
                          f"> {config['chain_manager']['base_path']}/{chain_name}/chain.log;"
        else:
            genesis_address = f"http://{config['chain_manager']['chain'][chain_name]['persistent_peers'][0]['host']}:" \
                                     f"{config['chain_manager']['chain'][chain_name]['persistent_peers'][0]['port']}"
            genesis = requests.get(f"{genesis_address}/genesis").json()['result']['genesis']
            with open(f"{config['chain_manager']['base_path']}/{chain_name}/config/genesis.json", 'w') as f:
                f.write(json.dumps(genesis))
            persistent_peers = []
            for persistent_peer in config['chain_manager']['chain'][chain_name]['persistent_peers']:
                response = requests.get(f"http://{persistent_peer['host']}:{persistent_peer['port']}/status").json()
                persistent_peers_id = response['result']['node_info']['id']
                persistent_peers_p2p_port = response['result']['node_info']['listen_addr'].split(':')[-1]
                persistent_peers.append(f"{persistent_peers_id}@{persistent_peer['host']}:{persistent_peers_p2p_port}")
            start_chain = f"tendermint start --home {config['chain_manager']['base_path']}/{chain_name} " \
                          f"--p2p.persistent_peers=\"{', '.join(persistent_peers)}\" " \
                          f"> {config['chain_manager']['base_path']}/{chain_name}/chain.log;"
        chain_pid = subprocess.Popen(start_chain,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        return chain_pid

    def _start_service(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        start_service = f"python {config['chain_manager']['chain'][chain_name]['type']}/service/service.py " \
                        f"{config['chain_manager']['chain'][chain_name]['abci_port']} " \
                        f"{config['app']['app_id']} " \
                        f"{config['chain_manager']['base_path']}/{chain_name} " \
                        f"{config['dock']['address']['port']} " \
                        f"> {config['chain_manager']['base_path']}/{chain_name}/service.log;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        return service_pid

    def _wait_for_chain_start(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        location = ("localhost", int(config['chain_manager']['chain'][chain_name]['rpc_port']))
        start_time = datetime.datetime.now()
        timeout = 15
        while True:
            if a_socket.connect_ex(location) == 0:
                break
            if (datetime.datetime.now() - start_time).seconds > timeout:
                break

    def get_chain_id(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        with open(f"{config['chain_manager']['base_path']}/{chain_name}/config/genesis.json") as file:
            genesis = yaml.load(file, Loader=yaml.Loader)
        chain_id = genesis['chain_id']
        return chain_id

    def add_chain(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        chain_pid = self._start_chain_core(chain_name)
        service_pid = self._start_service(chain_name)
        self._wait_for_chain_start(chain_name)
        chain_id = self.get_chain_id(chain_name)
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])
        log.info(f'{chain_name.capitalize()}({chain_id}) started')

    def start_chain(self, chain_id):
        chain_name = self._chains[chain_id].chain_name
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        chain_pid = self._start_chain_core(chain_name)
        service_pid = self._start_service(chain_name)
        self._wait_for_chain_start(chain_name)
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])
        log.info(f'{chain_name.capitalize()}({chain_id}) started')

    def join_chain(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        chain_pid = self._start_chain_core(chain_name, True)
        service_pid = self._start_service(chain_name)
        self._wait_for_chain_start(chain_name)
        chain_id = self.get_chain_id(chain_name)
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])
        with open(f"{config['chain_manager']['base_path']}/{chain_name}/config/priv_validator_key.json") as file:
            validator = yaml.load(file, Loader=yaml.Loader)
            message = {
                "header": {
                    "type": "validate",
                    "ttl": -1,
                    "index": -1,
                    "paths": [],
                    "source_chain_id": '',
                    "target_chain_id": '',
                    "auth": {
                        "app_id": config['app']['app_id'],
                        "app_info": ""
                    }
                },
                "body": {
                    "public_key": validator['pub_key']['value'],
                    "power": 10
                }
            }
        params = (
            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        requests.get(f"http://localhost:{self._chains[chain_id].rpc_port}/broadcast_tx_commit", params=params)
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])
        log.info(f'{chain_name.capitalize()}({chain_id}) started')

    def stop_chain(self, chain_id):
        chain_pid = self._chains[chain_id].chain_pid
        os.killpg(os.getpgid(chain_pid), signal.SIGTERM)
        service_pid = self._chains[chain_id].service_pid
        os.killpg(os.getpgid(service_pid), signal.SIGTERM)
        log.info(f'{self._chains[chain_id].chain_name.capitalize()} stopped')

    def delete_chain(self, chain_id):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        chain_name = self._chains[chain_id].chain_name
        with open(f"{config['chain_manager']['base_path']}/{chain_name}/config/priv_validator_key.json") as file:
            validator = yaml.load(file, Loader=yaml.Loader)
            message = {
                "header": {
                    "type": "validate",
                    "ttl": -1,
                    "paths": [],
                    "source_chain_id": '',
                    "target_chain_id": '',
                    "auth": {
                        "app_id": config['app']['app_id'],
                        "app_info": ""
                    },
                    "timestamp": str(time.time())
                },
                "body": {
                    "public_key": validator['pub_key']['value'],
                    "power": 0
                }
            }
        params = (
            ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
        )
        requests.get(f"http://localhost:{self._chains[chain_id].rpc_port}/broadcast_tx_commit", params=params)
        try:
            message = {
                "header": {
                    "type": "empty",
                    "ttl": -1,
                    "paths": [],
                    "source_chain_id": '',
                    "target_chain_id": '',
                    "auth": {
                        "app_id": config['app']['app_id'],
                        "app_info": ""
                    },
                    "timestamp": str(time.time())
                },
                "body": {}
            }
            params = (
                ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
            )
            requests.get(f"http://localhost:{self._chains[chain_id].rpc_port}/broadcast_tx_commit", params=params)
        except Exception as exception:
            log.info(repr(exception))
        self.stop_chain(chain_id)
        del self._chains[chain_id]
        remove_path = f"rm -rf {config['chain_manager']['base_path']}/{chain_name}"
        subprocess.run(remove_path,
                       shell=True,
                       stdout=subprocess.PIPE)
