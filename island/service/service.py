"""
Simple counting app.  It only accepts values sent to it in correct order.  The
state maintains the current count. For example, if starting at state 0, sending:
-> 0x01 = OK!
-> 0x03 = Will fail! (expects 2)

To run it:
- make a clean new directory for tendermint
- start this server: python counter.py
- start tendermint: tendermint --home "YOUR DIR HERE" node
- The send transactions to the app:


curl http://localhost:26657/broadcast_tx_commit?tx=0x01
curl http://localhost:26657/broadcast_tx_commit?tx=0x02
...

To see the latest count:
curl http://localhost:26657/abci_query

The way the app state is structured, you can also see the current state value
in the tendermint console output (see app_hash).
"""
import struct
import os
import sys
import json
import yaml
import grpc
import plyvel
import requests
import base64
import hashlib
from log import init_log, log
from interface.dci import dci_pb2_grpc, dci_pb2

from interface.sci.abci import types_pb2
from interface.sci.crypto import keys_pb2

from base.server import ABCIServer
from base.application import BaseApplication, OkCode, ErrorCode


def encode_number(value):
    return struct.pack(">I", value)


def decode_number(raw):
    return int.from_bytes(raw, byteorder="big")


class IslandService(BaseApplication):
    def __init__(self, db_path, dock_port, rpc_port):
        self.db_path = db_path
        self.dock_port = dock_port
        self.rpc_port = rpc_port
        self.world_state = plyvel.DB(os.path.join(db_path, 'world_state'), create_if_missing=True)
        self.graph_state = plyvel.DB(os.path.join(db_path, 'graph_state'), create_if_missing=True)
        self.route_state = plyvel.DB(os.path.join(db_path, 'route_state'), create_if_missing=True)
        self.last_block_height = None
        self.validator_updates = []
        self.address_to_public_key = {}

    def info(self, req) -> types_pb2.ResponseInfo:
        """
        Since this will always respond with height=0, Tendermint
        will resync this app from the beginning
        """
        r = types_pb2.ResponseInfo()
        r.version = req.version
        r.last_block_height = 0
        r.last_block_app_hash = b""
        return r

    def update_validator(self, validator_update):
        address = hashlib.sha256(
            validator_update.pub_key.ed25519).hexdigest()[0: 40]
        if validator_update.power == 0:
            self.address_to_public_key.pop(address)
        else:
            self.address_to_public_key[address] = validator_update.pub_key
        self.validator_updates.append(validator_update)

    def init_chain(self, request) -> types_pb2.ResponseInitChain:
        for validator in request.validators:
            self.update_validator(validator)
        self.last_block_height = 0
        return types_pb2.ResponseInitChain()

    def check_tx(self, tx) -> types_pb2.ResponseCheckTx:
        try:
            tx_json = json.loads(tx.decode('utf-8'))
            log.info(f'Check for tx {tx_json}')
        except Exception as exception:
            log.error(repr(exception))
            return types_pb2.ResponseCheckTx(code=ErrorCode)
        return types_pb2.ResponseCheckTx(code=OkCode)

    def deliver_tx(self, tx) -> types_pb2.ResponseDeliverTx:
        try:
            tx_json = json.loads(tx.decode('utf-8'))
            log.info(f'Received tx {tx_json}')
            message_type = tx_json['header']['type']
            if message_type == 'write':
                key = tx_json['body']['key']
                self.world_state.put(key.encode('utf-8'), json.dumps(tx_json['body']['value']).encode('utf-8'))
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'route':
                key = tx_json['body']['key']
                self.route_state.put(key.encode('utf-8'), json.dumps(tx_json['body']['value']).encode('utf-8'))
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'move':
                source_key = tx_json['body']['source_key']
                target_key = tx_json['body']['target_key']
                amount = tx_json['body']['amount']
                if amount != -1:
                    source_value = json.loads(self.world_state.get(source_key.encode('utf-8')).decode('utf-8'))
                    target_value = json.loads(self.world_state.get(target_key.encode('utf-8'),
                                                                   json.dumps(0).encode('utf-8')).decode('utf-8'))
                    if source_value - amount == 0:
                        self.world_state.delete(source_key.encode('utf-8'))
                    else:
                        self.world_state.put(source_key.encode('utf-8'), json.dumps(source_value - amount).encode('utf-8'))
                    self.world_state.put(target_key.encode('utf-8'), json.dumps(target_value + amount).encode('utf-8'))
                else:
                    value = self.world_state.get(source_key.encode('utf-8'))
                    self.world_state.delete(source_key.encode('utf-8'))
                    self.world_state.put(target_key.encode('utf-8'), value)
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'delete':
                key = tx_json['body']['key']
                self.world_state.delete(key.encode('utf-8'))
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'shard':
                request_shard = dci_pb2.RequestShard(graph_state=json.dumps(tx_json['body']['graph_state']))
                with grpc.insecure_channel(f'localhost:{self.dock_port}') as channel:
                    log.info('Call dock grpc: Shard')
                    client = dci_pb2_grpc.DockStub(channel)
                    response = client.Shard(request_shard)
                    log.info(f'Dock return with status code: {response.code}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'switch':
                with open(os.path.join(self.db_path, 'config/priv_validator_key.json')) as file:
                    priv_validator_key = yaml.load(file, Loader=yaml.Loader)
                node_id = priv_validator_key['address']
                if node_id == tx_json['body']['node_id']:
                    with grpc.insecure_channel(f'localhost:{self.dock_port}') as channel:
                        log.info('Call dock grpc: Switch')
                        request_switch_package = dci_pb2.RequestSwitch(chain_id=tx_json['body']['chain_id'])
                        client = dci_pb2_grpc.DockStub(channel)
                        response = client.Switch(request_switch_package)
                        log.info(f'Dock return with status code: {response.code}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'cross_write':
                request_tx_package = dci_pb2.RequestDeliverTx(tx=json.dumps(tx_json).encode('utf-8'))
                with grpc.insecure_channel(f'localhost:{self.dock_port}') as channel:
                    log.info('Call dock grpc: DeliverTx')
                    client = dci_pb2_grpc.DockStub(channel)
                    response = client.DeliverTx(request_tx_package)
                    log.info(f'Dock return with status code: {response.code}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'cross_move_source':
                source_key = tx_json['body']['source_key']
                amount = tx_json['body']['amount']
                if amount != -1:
                    source_value = json.loads(self.world_state.get(source_key.encode('utf-8')).decode('utf-8'))
                    lock_value = {
                        '_old_value': source_value,
                        '_new_value': source_value - amount
                    }
                    self.world_state.put(f'_{source_key}'.encode('utf-8'), json.dumps(lock_value).encode('utf-8'))
                    self.world_state.delete(source_key.encode('utf-8'))
                else:
                    value = json.loads(self.world_state.get(source_key.encode('utf-8')).decode('utf-8'))
                    lock_value = {
                        '_old_value': value
                    }
                    self.world_state.delete(source_key.encode('utf-8'))
                    self.world_state.put(f'_{source_key}'.encode('utf-8'), json.dumps(lock_value).encode('utf-8'))
                    tx_json['body']['value'] = value
                self._add_edge(tx_json['header'])
                request_tx_package = dci_pb2.RequestDeliverTx(tx=json.dumps(tx_json).encode('utf-8'))
                with grpc.insecure_channel(f'localhost:{self.dock_port}') as channel:
                    log.info('Call dock grpc: DeliverTx')
                    client = dci_pb2_grpc.DockStub(channel)
                    response = client.DeliverTx(request_tx_package)
                    log.info(f'Dock return with status code: {response.code}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'cross_move_target':
                target_key = tx_json['body']['target_key']
                amount = tx_json['body']['amount']
                if amount != -1:
                    target_value = json.loads(self.world_state.get(target_key.encode('utf-8'), default=json.dumps(0).encode('utf-8')).decode('utf-8'))
                    self.world_state.put(target_key.encode('utf-8'), json.dumps(target_value + amount).encode('utf-8'))
                else:
                    value = tx_json['body']['value']
                    self.world_state.put(target_key.encode('utf-8'), json.dumps(value).encode('utf-8'))
                unlock_json = {
                    "header": {
                        "type": "unlock",
                        "cross": {
                            "ttl": -1,
                            "paths": [],
                            "source_chain_id": tx_json['header']['cross']['target_chain_id'],
                            "source_node_id": tx_json['header']['cross']['target_node_id'],
                            "source_info": tx_json['header']['cross']['target_info'],
                            "target_chain_id": tx_json['header']['cross']['source_chain_id'],
                            "target_node_id": tx_json['header']['cross']['source_node_id'],
                            "target_info": tx_json['header']['cross']['source_info'],
                        },
                        "timestamp": tx_json['header']['timestamp']
                    },
                    'body': {
                        'key': tx_json['body']['source_key'],
                        'status': 0
                    }
                }
                request_tx_package = dci_pb2.RequestDeliverTx(tx=json.dumps(unlock_json).encode('utf-8'))
                with grpc.insecure_channel(f'localhost:{self.dock_port}') as channel:
                    log.info('Call dock grpc: DeliverTx')
                    client = dci_pb2_grpc.DockStub(channel)
                    response = client.DeliverTx(request_tx_package)
                    log.info(f'Dock return with status code: {response.code}')
                self._add_edge(tx_json['header'])
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'unlock':
                status = tx_json['body']['status']
                key = tx_json['body']['key']
                value = json.loads(self.world_state.get(f'_{key}'.encode('utf-8')).decode('utf-8'))
                self.world_state.delete(f'_{key}'.encode('utf-8'))
                if status == 0:
                    if value.get('_new_value') is not None:
                        self.world_state.put(key.encode('utf-8'), json.dumps(value['_new_value']).encode('utf-8'))
                else:
                    self.world_state.put(key.encode('utf-8'), json.dumps(value['_old_value']).encode('utf-8'))
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'validate':
                validator_update = types_pb2.ValidatorUpdate(
                    pub_key=keys_pb2.PublicKey(ed25519=base64.b64decode(tx_json['body']['public_key'])),
                    power=tx_json['body']['power'])
                self.update_validator(validator_update)
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'join':
                request_tx_package = dci_pb2.RequestDeliverTx(tx=json.dumps(tx_json).encode('utf-8'))
                with grpc.insecure_channel(f'localhost:{self.dock_port}') as channel:
                    log.info('Call dock grpc: DeliverTx')
                    client = dci_pb2_grpc.DockStub(channel)
                    response = client.DeliverTx(request_tx_package)
                    log.info(f'Dock return with status code: {response.code}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'empty':
                return types_pb2.ResponseDeliverTx(code=OkCode)
            else:
                raise Exception('Type error')
        except Exception as exception:
            log.error(repr(exception))
            return types_pb2.ResponseDeliverTx(code=ErrorCode, data=repr(exception).encode('utf-8'))

    def _add_edge(self, header):
        node_pair = {
            'source_node_id': header['cross']['source_node_id'],
            'target_node_id': header['cross']['target_node_id'],
        }
        default_value = {
            'source_chain_id': header['cross']['source_chain_id'],
            'source_info': header['cross']['source_info'],
            'target_chain_id': header['cross']['source_chain_id'],
            'target_info': header['cross']['target_info'],
            'weight': [],
        }
        value = self.graph_state.get(json.dumps(node_pair).encode('utf-8'), default=json.dumps(default_value).encode('utf-8'))
        edge = json.loads(value.decode('utf-8'))
        if len(edge['weight']) > 100:
            edge['weight'].pop(0)
        edge['weight'].append(header['timestamp'])
        self.graph_state.put(json.dumps(node_pair).encode('utf-8'), json.dumps(edge).encode('utf-8'))

    def query(self, req) -> types_pb2.ResponseQuery:
        try:
            tx_json = json.loads(req.data.decode('utf-8'))
            message_type = tx_json['header']['type']
            if message_type == 'read':
                key = tx_json['body']['key']
                value = self.world_state.get(key.encode('utf-8'))
                return types_pb2.ResponseQuery(code=OkCode, value=value)
            elif message_type == 'graph':
                graph_data = [{'source_node_id': json.loads(key.decode('utf-8'))['source_node_id'],
                               'source_info': json.loads(value.decode('utf-8'))['source_info'],
                               'source_chain_id': json.loads(value.decode('utf-8'))['source_chain_id'],
                               'target_node_id': json.loads(key.decode('utf-8'))['target_node_id'],
                               'target_info': json.loads(value.decode('utf-8'))['target_info'],
                               'target_chain_id': json.loads(value.decode('utf-8'))['target_chain_id'],
                               'weight': json.loads(value.decode('utf-8'))['weight']} for key, value in self.graph_state.iterator()]
                return types_pb2.ResponseQuery(code=OkCode, value=json.dumps(graph_data).encode('utf-8'))
            elif message_type == 'route':
                key = tx_json['body']['key']
                value = self.route_state.get(key.encode('utf-8'), default=json.dumps(0).encode('utf-8'))
                return types_pb2.ResponseQuery(code=OkCode, value=value)
            else:
                raise Exception('Type error')
        except Exception as exception:
            log.error(repr(exception))
            return types_pb2.ResponseQuery(code=ErrorCode, value=repr(exception).encode('utf-8'))

    def commit(self) -> types_pb2.ResponseCommit:
        """Return the current encode state value to tendermint"""
        hash = struct.pack(">Q", self.last_block_height)
        return types_pb2.ResponseCommit(data=hash)

    def begin_block(self, req: types_pb2.RequestBeginBlock) -> types_pb2.ResponseBeginBlock:
        self.validator_updates = []
        return types_pb2.ResponseBeginBlock()

    def end_block(self, req: types_pb2.RequestEndBlock) -> types_pb2.ResponseEndBlock:
        # if req.height % 100 == 0:
        #     message = {
        #         "header": {
        #             "type": "shard",
        #             "nonce": self.last_block_height,
        #         },
        #         "body": {
        #             'graph_state': [{'source_node_id': json.loads(key.decode('utf-8'))['source_node_id'],
        #                              'source_info': json.loads(value.decode('utf-8'))['source_info'],
        #                              'source_chain_id': json.loads(value.decode('utf-8'))['source_chain_id'],
        #                              'target_node_id': json.loads(key.decode('utf-8'))['target_node_id'],
        #                              'target_info': json.loads(value.decode('utf-8'))['target_info'],
        #                              'target_chain_id': json.loads(value.decode('utf-8'))['target_chain_id'],
        #                              'weight': json.loads(value.decode('utf-8'))['weight']} for key, value in self.graph_state.iterator()]
        #         }
        #     }
        #     for key, value in self.graph_state.iterator():
        #         self.graph_state.delete(key)
        #     params = (
        #         ('tx', '0x' + json.dumps(message).encode('utf-8').hex()),
        #     )
        #     requests.get(f"http://localhost:{self.rpc_port}/broadcast_tx_async", params=params)
        return types_pb2.ResponseEndBlock(validator_updates=self.validator_updates)


def main(args):
    init_log(args[5])
    app = ABCIServer(app=IslandService(args[2], args[3], args[4]), port=args[1])
    app.run()


if __name__ == "__main__":
    main(sys.argv)
