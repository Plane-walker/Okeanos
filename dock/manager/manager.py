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
        if chain_type == 'island':
            log.info('Creating island chain')
            for chain_sequence in range(config['chain_manager']['island']['number']):
                init_island = f"tendermint init --home {config['chain_manager']['island']['base_path']}/island &> /dev/null;" \
                              f"sed -i " \
                              f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['chain_manager']['island']['abci_port'][chain_sequence]}\"#g' " \
                              f"{config['chain_manager']['island']['base_path']}/island/config/config.toml &> /dev/null;" \
                              f"sed -i " \
                              f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://127.0.0.1:{config['chain_manager']['island']['rpc_port'][chain_sequence]}\"#g' " \
                              f"{config['chain_manager']['island']['base_path']}/island/config/config.toml &> /dev/null;" \
                              f"sed -i " \
                              f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['chain_manager']['island']['p2p_port'][chain_sequence]}\"#g' " \
                              f"{config['chain_manager']['island']['base_path']}/island/config/config.toml &> /dev/null;"
                subprocess.run(init_island, shell=True, stdout=subprocess.PIPE)
                start_island = f"tendermint start --home {config['chain_manager']['island']['base_path']}/island &> /dev/null"
                self.island_process.append(subprocess.Popen(start_island,
                                                            shell=True,
                                                            stdout=subprocess.PIPE,
                                                            preexec_fn=os.setsid))
                log.info('Island chain created')
        elif chain_type == 'lane':
            for chain_sequence in range(config['chain_manager']['island']['number']):
                log.info(f'Creating lane chain {chain_sequence}')
                init_lane = f"tendermint init --home {config['chain_manager']['lane']['base_path']}/lane_{chain_sequence} &> /dev/null;" \
                            f"sed -i " \
                            f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['chain_manager']['lane']['abci_port'][chain_sequence]}\"#g' " \
                            f"{config['chain_manager']['lane']['base_path']}/lane_{chain_sequence}/config/config.toml &> /dev/null;" \
                            f"sed -i " \
                            f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://127.0.0.1:{config['chain_manager']['lane']['rpc_port'][chain_sequence]}\"#g' " \
                            f"{config['chain_manager']['lane']['base_path']}/lane_{chain_sequence}/config/config.toml &> /dev/null;" \
                            f"sed -i " \
                            f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['chain_manager']['lane']['p2p_port'][chain_sequence]}\"#g' " \
                            f"{config['chain_manager']['lane']['base_path']}/lane_{chain_sequence}/config/config.toml &> /dev/null;"
                subprocess.run(init_lane, shell=True, stdout=subprocess.PIPE)
                start_lane = f"tendermint start --home {config['chain_manager']['lane']['base_path']}/lane_{chain_sequence} &> /dev/null"
                self.lane_process.append(subprocess.Popen(start_lane,
                                                          shell=True,
                                                          stdout=subprocess.PIPE,
                                                          preexec_fn=os.setsid))
                log.info(f'Lane chain {chain_sequence} created')

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
