__all__ = [
    'RouteMessage',
]

import json


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
            return cls(header['source_chain_id'], header['target_chain_id'],
                       header['type'], header['paths'], header['ttl'], body)

    @classmethod
    def from_data(cls,
                  source,
                  target,
                  typ=None,
                  ttl=None,
                  paths=None):
        body = {}
        return cls(source, target, typ, paths, ttl, body)

    def __init__(self, source: str, target: str, typ, paths, ttl, body):
        self.header = {
            'source': source,
            'target': target,
        }
        self.body = body if body is not None else {}
        if typ is not None:
            self.header['type'] = typ
        if paths is not None:
            self.header['paths'] = paths
        self.header['ttl'] = ttl if ttl is not None else -1

    def target_id(self):
        return self.header['target']

    def source_id(self):
        return self.header['source']

    def get_type(self):
        return self.header['type'] if 'type' in self.header else None

    def set_type(self, typ):
        self.header['type'] = typ

    def init_paths(self):
        self.header['paths'] = []

    def empty_path(self):
        return len(self.header['paths']) == 0

    def pop_path(self):
        if 'paths' in self.header and len(self.header['paths']) > 0:
            self.header['paths'].pop()

    def append_path(self, lane_id: str, island_id: str):
        path = (lane_id, island_id)
        if 'paths' in self.header:
            self.header['paths'].append(path)
        else:
            self.header['paths'] = [path]

    def get_paths_copy(self):
        if 'paths' in self.header:
            return self.header['paths'].copy()
        return None

    def get_paths_islands_copy(self):
        if 'paths' in self.header:
            return [path[1] for path in self.header['paths']]
        return None

    def get_paths_lanes_copy(self):
        return [path[0] for path in self.header['paths']]

    def last_path_lane(self):
        if 'paths' in self.header and len(self.header['paths']) > 0:
            return self.header['paths'][-1][0]
        return None

    def get_path_lane(self, index):
        if index >= 0:
            return self.header['paths'][index][0] if 'paths' in self.header and \
                index < len(self.header['paths']) else None
        return None

    def get_ttl(self) -> int:
        return self.header['ttl'] if 'ttl' in self.header else None

    def set_ttl(self, ttl):
        self.header['ttl'] = ttl

    def reduce_ttl(self):
        if 'ttl' in self.header:
            self.header['ttl'] -= 1

    def is_transmit(self) -> bool:
        return 'ttl' in self.header and self.header['ttl'] >= 0

    def is_callback(self) -> bool:
        return 'ttl' in self.header and self.header['ttl'] < 0

    def get_json(self):
        header = {
            'ttl': self.header['ttl'],
            'source_chain_id': self.header['source'],
            'target_chain_id': self.header['target'],
            'paths': self.header['paths'],
            'type': self.header['type']
        }
        msg = {'header': header, 'body': {}}
        return json.dumps(msg).encode('utf-8')

    def get_hex(self) -> str:
        return '0x' + self.get_json().hex()

    def to_callback(self):
        source = self.header['source']
        self.header['source'] = self.header['target']
        self.header['target'] = source
        self.header['type'] = 'route'
        self.header['ttl'] = -1
