__all__ = [
    'ChainManager'
]

import os
import subprocess
import signal


class ChainManager:
    def __init__(self, island_process=None):
        self.island_process = island_process

    def create_chain(self, chain_type):
        if chain_type == 'island':
            self.island_process = subprocess.Popen(f"tendermint start --home /root/island &> /dev/null",
                                                   shell=True,
                                                   stdout=subprocess.PIPE,
                                                   preexec_fn=os.setsid)

    def stop_chain(self, chain_type):
        if chain_type == 'island':
            os.killpg(os.getpgid(self.island_process.pid), signal.SIGTERM)

    def join_chain(self):
        pass

    def leave_chain(self):
        pass
