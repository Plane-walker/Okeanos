__all__ = [
    'ChainManager'
]

import os
import shutil
import subprocess
import signal
import yaml
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
        init_chain = f"tendermint init --home {config['chain_manager']['base_path']}/{chain_name} &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['chain_manager']['chain'][chain_name]['abci_port']}\"#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://0.0.0.0:{config['chain_manager']['chain'][chain_name]['rpc_port']}\"#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['chain_manager']['chain'][chain_name]['p2p_port']}\"#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#create_empty_blocks = true#create_empty_blocks = false#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#addr_book_strict = true#addr_book_strict = false#g' " \
                     f"{config['chain_manager']['base_path']}/{chain_name}/config/config.toml &> /dev/null;"
        subprocess.run(init_chain, shell=True, stdout=subprocess.PIPE)

    def add_chain(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        start_chain = f"tendermint start --home {config['chain_manager']['base_path']}/{chain_name} " \
                      f"> {config['chain_manager']['base_path']}/{chain_name}/chain_log.txt;"
        chain_pid = subprocess.Popen(start_chain,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        start_service = f"python {config['chain_manager']['chain'][chain_name]['type']}/service/service.py {config['chain_manager']['chain'][chain_name]['abci_port']} " \
                        f"{config['chain_manager']['base_path']}/{chain_name} " \
                        f"> {config['chain_manager']['base_path']}/{chain_name}/service_log.txt;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        with open(f"{config['chain_manager']['base_path']}/{chain_name}/config/genesis.json") as file:
            genesis = yaml.load(file, Loader=yaml.Loader)
        chain_id = genesis['chain_id']
        log.info(f'{chain_name.capitalize()}({chain_id}) started')
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])

    def start_chain(self, chain_id):
        chain_name = self._chains[chain_id].chain_name
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        start_chain = f"tendermint start --home {config['chain_manager']['base_path']}/{chain_name} " \
                      f"> {config['chain_manager']['base_path']}/{chain_name}/chain_log.txt;"
        chain_pid = subprocess.Popen(start_chain,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        start_service = f"python {config['chain_manager']['chain'][chain_name]['type']}/service/service.py {config['chain_manager']['chain'][chain_name]['abci_port']} " \
                        f"{config['chain_manager']['base_path']}/{chain_name} " \
                        f"> {config['chain_manager']['base_path']}/{chain_name}/service_log.txt;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        log.info(f'{chain_name.capitalize()} started')
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])

    def join_chain(self, chain_name):
        with open(self._config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        shutil.copy(f"{config['chain_manager']['base_path']}/{config['chain_manager']['chain'][chain_name]['genesis_path']}/genesis.json",
                    f"{config['chain_manager']['base_path']}/{chain_name}/config/genesis.json")
        start_chain = f"tendermint start --home {config['chain_manager']['base_path']}/{chain_name} " \
                      f"--p2p.persistent_peers=\"{', '.join(config['chain_manager']['chain'][chain_name]['persistent_peers'])}\""
        chain_pid = subprocess.Popen(start_chain,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        start_service = f"python {config['chain_manager']['chain'][chain_name]['type']}/service/service.py {config['chain_manager']['chain'][chain_name]['abci_port']} " \
                        f"{config['chain_manager']['base_path']}/{chain_name} " \
                        f"> {config['chain_manager']['base_path']}/{chain_name}/service_log.txt;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        with open(f"{config['chain_manager']['base_path']}/{chain_name}/config/genesis.json") as file:
            genesis = yaml.load(file, Loader=yaml.Loader)
        chain_id = genesis['chain_id']
        self._chains[chain_id] = BaseChain(config['chain_manager']['chain'][chain_name]['type'],
                                           chain_id,
                                           chain_pid,
                                           service_pid,
                                           chain_name,
                                           config['chain_manager']['chain'][chain_name]['rpc_port'])

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
        self.stop_chain(chain_id)
        remove_path = f"rm -rf {config['chain_manager']['base_path']}/{chain_name}"
        subprocess.run(remove_path,
                       shell=True,
                       stdout=subprocess.PIPE)
