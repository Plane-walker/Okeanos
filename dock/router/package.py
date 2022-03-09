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
                       header['type'], header['paths'], header['ttl'],
                       header['index'])

    @classmethod
    def from_data(cls,
                  source,
                  target,
                  typ=None,
                  ttl=None,
                  paths=None,
                  index=None):
        return cls(source, target, typ, paths, ttl, index)

    def __init__(self, source: str, target: str, typ, paths, ttl, index):
        self.data = {
            'source': source,
            'target': target,
        }
        if typ is not None:
            self.data['type'] = typ
        if paths is not None:
            self.data['paths'] = paths
        self.data['ttl'] = ttl if ttl is not None else -1
        self.data['index'] = index if index is not None else -1

    def target_id(self):
        return self.data['target']

    def source_id(self):
        return self.data['source']

    def get_type(self):
        return self.data['type'] if 'type' in self.data else None

    def set_type(self, typ):
        self.data['type'] = typ

    def init_paths(self):
        self.data['paths'] = []

    def pop_path(self):
        if 'paths' in self.data and len(self.data['paths']) > 0:
            self.data['paths'].pop()

    def append_path(self, path: str):
        if 'paths' in self.data:
            self.data['paths'].append(path)
        else:
            self.data['paths'] = [path]

    def get_paths_copy(self):
        if 'paths' in self.data:
            return self.data['paths'].copy()
        return None

    def last_path(self):
        if 'paths' in self.data and len(self.data['paths']) > 0:
            return self.data['paths'][-1]
        return None

    def get_path(self, index):
        if index >= 0:
            return self.data['paths'][index] if 'paths' in self.data and \
                index < len(self.data['paths']) else None
        return None

    def get_ttl(self) -> int:
        return self.data['ttl'] if 'ttl' in self.data else None

    def set_ttl(self, ttl):
        self.data['ttl'] = ttl

    def reduce_ttl(self):
        if 'ttl' in self.data:
            self.data['ttl'] -= 1

    def is_transmit(self) -> bool:
        return 'ttl' in self.data and self.data['ttl'] >= 0

    def is_callback(self) -> bool:
        return 'ttl' in self.data and self.data['ttl'] < 0

    def get_index(self):
        return self.data['index']

    def reduce_index(self):
        if 'index' in self.data and self.data['index'] >= 0:
            self.data['index'] -= 1

    def get_json(self):
        header = {
            'ttl': self.data['ttl'],
            'source_chain_id': self.data['source'],
            'target_chain_id': self.data['target'],
            'paths': self.data['paths'],
            'index': self.data['index'],
            'type': self.data['type']
        }
        msg = {'header': header, 'body': {}}
        return json.dumps(msg).encode('utf-8')

    def get_hex(self) -> str:
        return '0x' + self.get_json().hex()

    def to_callback(self):
        source = self.data['source']
        self.data['source'] = self.data['target']
        self.data['target'] = source
        self.data['type'] = 'route'
        self.data['index'] = len(self.data['paths']) - 1
        self.data['ttl'] = -1
