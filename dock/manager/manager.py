__all__ = [
    'ChainManager'
]

import os
import subprocess
import signal
import yaml
from log import log


class ChainManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.island_process = []
        self.lane_process = []

    def create_chain(self, chain_type):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        process = getattr(self, chain_type + '_process', None)
        process.clear()
        for chain_sequence in range(config['chain_manager'][chain_type]['number']):
            log.info(f'Creating {chain_type} chain {chain_sequence}')
            init_chain = f"tendermint init --home {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} &> /dev/null;" \
                          f"sed -i " \
                          f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['chain_manager'][chain_type]['abci_port'][chain_sequence]}\"#g' " \
                          f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/config.toml &> /dev/null;" \
                          f"sed -i " \
                          f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://127.0.0.1:{config['chain_manager'][chain_type]['rpc_port'][chain_sequence]}\"#g' " \
                          f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/config.toml &> /dev/null;" \
                          f"sed -i " \
                          f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['chain_manager'][chain_type]['p2p_port'][chain_sequence]}\"#g' " \
                          f"{config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/config/config.toml &> /dev/null;"
            subprocess.run(init_chain, shell=True, stdout=subprocess.PIPE)
            start_process = f"tendermint start --home {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} &> /dev/null"
            process.append(subprocess.Popen(start_process,
                                            shell=True,
                                            stdout=subprocess.PIPE,
                                            preexec_fn=os.setsid))
            log.info(f'{chain_type.capitalize()} chain {chain_sequence} created')

    def start_chain(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        process = getattr(self, chain_type + '_process', None)
        start_process = f"tendermint start --home {config['chain_manager'][chain_type]['base_path']}/{chain_type} &> /dev/null"
        process[chain_sequence] = subprocess.Popen(start_process,
                                                   shell=True,
                                                   stdout=subprocess.PIPE,
                                                   preexec_fn=os.setsid)

    def stop_chain(self, chain_type, chain_sequence):
        process = getattr(self, chain_type + '_process', None)
        if process is not None:
            os.killpg(os.getpgid(process[chain_sequence].pid), signal.SIGTERM)

    def join_chain(self):
        pass

    def leave_chain(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.stop_chain(self, chain_type, chain_sequence)
        remove_directory = f"rm -rf {config['chain_manager'][chain_type]['base_path']}/{chain_type} &> /dev/null"
        subprocess.run(remove_directory, shell=True, stdout=subprocess.PIPE)
