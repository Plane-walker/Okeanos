__all__ = [
    'Message',
]


import json
from interface.dci.dci_pb2 import RequestDeliverTx


class Message:

    types = ['route', 'cross', 'normal', 'graph', 'validate']

    @classmethod
    def from_req(cls, req):
        if req is None or not isinstance(req, RequestDeliverTx):
            raise TypeError('req must be RequestDeliverTx')
        message = json.loads(req.tx.decode('utf-8'))
        if 'header' not in message or message['header'] is None:
            raise ValueError('req must have header')
        if 'body' not in message or message['body'] is None:
            raise ValueError('req must have body')
        return cls(message['header'], message['body'])

    def __init__(self, header, body):
        self.header = header
        self.body = body
        self.msg = {
            'header': self.header,
            'body': self.body
        }

    def get_type(self):
        return self.header['type']

    def set_type(self, typ):
        if typ not in self.types:
            raise ValueError('type must be one of %s' % self.types)
        self.header['type'] = typ

    def get_json(self):
        return json.dumps(self.msg).encode('utf-8')

    def get_hex(self) -> str:
        return '0x' + json.dumps(self.msg).encode('utf-8').hex()
