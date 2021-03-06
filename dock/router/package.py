__all__ = [
    'RouteMessage',
]

import json
import time

class RouteMessage:

    @classmethod
    def from_tx(cls, tx):
        tx_json = None
        try:
            tx_json = json.loads(tx.decode('utf-8'))
        except Exception as exception:
            raise exception
        else:
            header = tx_json.get('header')
            body = tx_json.get('body')
            if header is None or body is None:
                raise ValueError('tx must have header and body')
            return cls(header, body)

    @classmethod
    def from_data(cls,
                  source_chain_id,
                  source_node_id,
                  source_info,
                  target_chain_id,
                  target_node_id,
                  target_info,
                  typ=None,
                  ttl=None,
                  paths=None):
        header = {
            'type': typ,
            'cross': {
                'ttl': ttl,
                'paths': [] if paths is None else paths,
                'source_chain_id': source_chain_id,
                'source_node_id': source_node_id,
                'source_info': source_info,
                'target_chain_id': target_chain_id,
                'target_node_id': target_node_id,
                'target_info': target_info,
            },
            'timestamp': str(time.time()),
        }
        body = {}
        return cls(header, body)

    def __init__(self, header, body):
        self.header = header
        self.body = body if body is not None else {}

    def target_id(self):
        return self.header['cross']['target_chain_id']

    def source_id(self):
        return self.header['cross']['source_chain_id']

    def get_type(self):
        return self.header['type'] if 'type' in self.header else None

    def set_type(self, typ):
        self.header['type'] = typ

    def init_paths(self):
        self.header['cross']['paths'] = []

    def empty_path(self):
        return len(self.header['cross']['paths']) == 0

    def pop_path(self):
        if 'paths' in self.header['cross'] and len(self.header['cross']['paths']) > 0:
            self.header['cross']['paths'].pop()

    def append_path(self, lane_id: str, island_id: str):
        path = (lane_id, island_id)
        if 'paths' in self.header['cross']:
            self.header['cross']['paths'].append(path)
        else:
            self.header['cross']['paths'] = [path]

    def get_paths_copy(self):
        if 'paths' in self.header['cross']:
            return self.header['cross']['paths'].copy()
        return None

    def get_paths_islands_copy(self):
        if 'paths' in self.header['cross']:
            return [path[1] for path in self.header['cross']['paths']]
        return None

    def get_paths_lanes_copy(self):
        return [path[0] for path in self.header['cross']['paths']]

    def last_path_lane(self):
        if 'paths' in self.header['cross'] and len(self.header['cross']['paths']) > 0:
            return self.header['cross']['paths'][-1][0]
        return None

    def get_path_lane(self, index):
        if index >= 0:
            return self.header['cross']['paths'][index][0] if 'paths' in self.header['cross'] and \
                index < len(self.header['cross']['paths']) else None
        return None

    def get_island_index(self, island_id):
        for index, path in enumerate(self.header['cross']['paths']):
            if path[1] == island_id:
                return index
        return -1

    def get_path(self, index):
        if index >= 0:
            return self.header['cross']['paths'][index] if 'paths' in self.header['cross'] and \
                index < len(self.header['cross']['paths']) else None
        return None

    def get_ttl(self) -> int:
        return self.header['cross']['ttl'] if 'ttl' in self.header['cross'] else None

    def set_ttl(self, ttl):
        self.header['cross']['ttl'] = ttl

    def reduce_ttl(self):
        if 'ttl' in self.header['cross']:
            self.header['cross']['ttl'] -= 1

    def is_transmit(self) -> bool:
        return 'ttl' in self.header['cross'] and self.header['cross']['ttl'] >= 0

    def is_callback(self) -> bool:
        return 'ttl' in self.header['cross'] and self.header['cross']['ttl'] < 0

    def get_json(self):
        msg = {'header': self.header, 'body': self.body}
        return json.dumps(msg).encode('utf-8')

    def get_hex(self) -> str:
        return '0x' + self.get_json().hex()

    def to_callback(self):
        source = self.header['cross']['source_chain_id']
        self.header['cross']['source_chain_id'] = self.header['cross']['target_chain_id']
        self.header['cross']['target_chain_id'] = source
        self.header['type'] = 'route'
        self.header['cross']['ttl'] = -1
