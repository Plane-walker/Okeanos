__all__ = [
    'ChainManager'
]

import os
import subprocess
import signal
import yaml
from log import log


class BaseChain:
    def __init__(self, chain_pid, service_pid, chain_type, chain_sequence, rpc_port):
        self.chain_pid = chain_pid
        self.service_pid = service_pid
        self.chain_type = chain_type
        self.chain_sequence = chain_sequence
        self.rpc_port = rpc_port


class ChainManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.chains = {}

    def init_chain(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        init_chain = f"tendermint init --home {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['chain_manager'][chain_type]['abci_port'][chain_sequence]}\"#g' " \
                     f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/config.toml &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://127.0.0.1:{config['chain_manager'][chain_type]['rpc_port'][chain_sequence]}\"#g' " \
                     f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/config.toml &> /dev/null;" \
                     f"sleep 3;" \
                     f"sed -i " \
                     f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['chain_manager'][chain_type]['p2p_port'][chain_sequence]}\"#g' " \
                     f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/config.toml &> /dev/null;"
        subprocess.run(init_chain, shell=True, stdout=subprocess.PIPE)

    def add_chain(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        start_chain = f"tendermint start --home {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} " \
                      f"> {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/chain_log.txt;"
        chain_pid = subprocess.Popen(start_chain,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        start_service = f"python {chain_type}/service/service.py {config['chain_manager'][chain_type]['abci_port'][chain_sequence]} {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} " \
                        f"> {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/service_log.txt;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        log.info(f'{chain_type.capitalize()} chain {chain_sequence} started')
        with open(f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/genesis.json") as file:
            genesis = yaml.load(file, Loader=yaml.Loader)
        chain_id = genesis['chain_id']
        self.chains[chain_id] = BaseChain(chain_pid, service_pid, chain_type, chain_sequence, config['chain_manager'][chain_type]['rpc_port'][chain_sequence])

    def start_chain(self, chain_id):
        chain_type = self.chains[chain_id].chain_type
        chain_sequence = self.chains[chain_id].chain_sequence
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        start_chain = f"tendermint start --home {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} " \
                      f"> {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/chain_log.txt;"
        chain_pid = subprocess.Popen(start_chain,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        start_service = f"python {chain_type}/service/service.py {config['chain_manager'][chain_type]['abci_port'][chain_sequence]} {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} " \
                        f"> {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/service_log.txt;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        log.info(f'{chain_type.capitalize()} chain {chain_sequence} started')
        self.chains[chain_id] = BaseChain(chain_pid, service_pid, chain_type, chain_sequence, config['chain_manager'][chain_type]['rpc_port'][chain_sequence])

    def join_chain(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.init_chain(chain_type, chain_sequence)
        start_command = f"tendermint start --home {config['join']['base_path']} --p2p.persistent_peers=\""
        for idx, peer in enumerate(config['join']['persistent_peers']):
            start_command += f"{peer}"
            if idx < len(config['join']['persistent_peers']) - 1:
                start_command += ','
        start_command += f"\"  > {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/chain_log.txt;"
        chain_pid = subprocess.Popen(start_command,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     preexec_fn=os.setsid).pid
        start_service = f"python {chain_type}/service/service.py {config['chain_manager'][chain_type]['abci_port'][chain_sequence]} {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} " \
                        f"> {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/service_log.txt;"
        service_pid = subprocess.Popen(start_service,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       preexec_fn=os.setsid).pid
        with open(f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/genesis.json") as file:
            genesis = yaml.load(file, Loader=yaml.Loader)
        chain_id = genesis['chain_id']
        self.chains[chain_id] = BaseChain(chain_pid, service_pid, chain_type, chain_sequence, config['chain_manager'][chain_type]['rpc_port'][chain_sequence])

    def stop_chain(self, chain_id):
        chain_pid = self.chains[chain_id].chain_pid
        os.killpg(os.getpgid(chain_pid), signal.SIGTERM)
        service_pid = self.chains[chain_id].service_pid
        os.killpg(os.getpgid(service_pid), signal.SIGTERM)
        log.info(f'{self.chains[chain_id].chain_type.capitalize()} chain {self.chains[chain_id].chain_sequence} stopped')

    def delete_chain(self, chain_id):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        chain_type = self.chains[chain_id].chain_type
        chain_sequence = self.chains[chain_id].chain_sequence
        self.stop_chain(chain_id)
        remove_path = f"rm -rf {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}"
        subprocess.run(remove_path,
                       shell=True,
                       stdout=subprocess.PIPE)
