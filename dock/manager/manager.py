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
        self.island_service = []
        self.lane_process = []
        self.lane_service = []

    def create_chain(self, chain_type):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        process = getattr(self, chain_type + '_process', None)
        service = getattr(self, chain_type + '_service', None)
        process.clear()
        for chain_sequence in range(config['chain_manager'][chain_type]['number']):
            log.info(f'Creating {chain_type} chain {chain_sequence}')
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
            start_process = f"tendermint start --home {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence} > {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/tendermint_log.txt"
            process.append(subprocess.Popen(start_process,
                                            shell=True,
                                            stdout=subprocess.PIPE,
                                            preexec_fn=os.setsid))
            start_service = f"python {chain_type}/service/service.py {config['chain_manager'][chain_type]['abci_port'][chain_sequence]} > {config['chain_manager'][chain_type]['base_path']}/{chain_type}_{chain_sequence}/service_log.txt"
            service.append(subprocess.Popen(start_service,
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

    def join_chain(self, chain_type):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        dir_name = f"{chain_type}" + (f"_{str(len(self.lane_process))}" if chain_type == 'lane' else "")
        init_command = f"tendermint init --home {config['join']['base_path']}/{dir_name} &> /dev/null;"
        init_command += f"sed -i " \
                        f"'s#proxy_app = \"tcp://127.0.0.1:26658\"#proxy_app = \"tcp://127.0.0.1:{config['join']['port']['abci']}\"#g' " \
                        f"{config['join']['base_path']}/{dir_name}/config/config.toml &> /dev/null;" \
                        f"sed -i " \
                        f"'s#laddr = \"tcp://127.0.0.1:26657\"#laddr = \"tcp://127.0.0.1:{config['join']['port']['rpc']}\"#g' " \
                        f"{config['join']['base_path']}/{dir_name}/config/config.toml &> /dev/null;" \
                        f"sed -i " \
                        f"'s#laddr = \"tcp://0.0.0.0:26656\"#laddr = \"tcp://0.0.0.0:{config['join']['port']['p2p']}\"#g' " \
                        f"{config['join']['base_path']}/{dir_name}/config/config.toml &> /dev/null;"
        subprocess.run(init_command, shell=True, stdout=subprocess.PIPE)
        start_command = f"tendermint start --home {config['join']['base_path']} --p2p.persistent_peers=\""
        for idx, peer in enumerate(config['join']['persistent_peers']):
            start_command += f"{peer}"
            if idx < len(config['join']['persistent_peers']) - 1:
                start_command += ','
        start_command += f"\"  &> /dev/null"
        process = getattr(self, chain_type + '_process', None)
        process.append(subprocess.Popen(start_command,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        preexec_fn=os.setsid))

    def stop_chain(self, chain_type, chain_sequence):
        process = getattr(self, chain_type + '_process', None)
        if process[chain_sequence] is not None:
            os.killpg(os.getpgid(process[chain_sequence].pid), signal.SIGTERM)

    def leave_chain(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.stop_chain(chain_type, chain_sequence)
        remove_directory = f"rm -rf {config['chain_manager'][chain_type]['base_path']}/{chain_type} &> /dev/null"
        subprocess.run(remove_directory, shell=True, stdout=subprocess.PIPE)

    def start_service(self, chain_type, chain_sequence):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        service = getattr(self, chain_type + '_service', None)
        start_process = f"python {chain_type}/service/service.py {config['chain_manager'][chain_type]['abci_port'][chain_sequence]} &> /dev/null"
        service[chain_sequence] = subprocess.Popen(start_process,
                                                   shell=True,
                                                   stdout=subprocess.PIPE,
                                                   preexec_fn=os.setsid)

    def stop_service(self, chain_type, chain_sequence):
        service = getattr(self, chain_type + '_service', None)
        if service[chain_sequence] is not None:
            os.killpg(os.getpgid(service[chain_sequence].pid), signal.SIGTERM)
