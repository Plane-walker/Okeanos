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
import grpc
import yaml
import leveldb
import base64
import hashlib
from log import init_log, log
from interface.dci import dci_pb2_grpc, dci_pb2
from interface.common import id_pb2

from interface.sci.abci import types_pb2
from interface.sci.crypto import keys_pb2

from base.server import ABCIServer
from base.application import BaseApplication, OkCode, ErrorCode


def encode_number(value):
    return struct.pack(">I", value)


def decode_number(raw):
    return int.from_bytes(raw, byteorder="big")


class IslandService(BaseApplication):
    def __init__(self, app_id, db_path):
        self.app_id = app_id
        self.db_path = db_path
        self.db = leveldb.LevelDB(os.path.join(db_path, 'db'))
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
        address = hashlib.sha256(validator_update.pub_key.ed25519).hexdigest()[0: 40]
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
            log.info(f'Check for tx {tx_json}({self.app_id})')
        except Exception as exception:
            log.error(repr(exception))
        return types_pb2.ResponseCheckTx(code=OkCode)

    def deliver_tx(self, tx) -> types_pb2.ResponseDeliverTx:
        tx_json = json.loads(tx.decode('utf-8'))
        log.info(f'Deliver tx {tx_json}({self.app_id})')
        if tx_json.get('validator') is not None:
            validator_update = types_pb2.ValidatorUpdate(pub_key=keys_pb2.PublicKey(ed25519=base64.b64decode(tx_json['validator']['public_key'])),
                                                         power=tx_json['validator']['power'])
            self.update_validator(validator_update)
        elif tx_json.get('target') is not None:
            request_tx_package = dci_pb2.RequestDeliverTx(
                tx=tx,
                target=id_pb2.Chain(identifier=tx_json['target']),
                source=id_pb2.Chain(identifier=tx_json['source']),
                flag=tx_json['flag']
            )
            with grpc.insecure_channel('localhost:1453') as channel:
                log.info('Call dock grpc: DeliverTx')
                client = dci_pb2_grpc.DockStub(channel)
                response = next(client.DeliverTx(request_tx_package))
                log.info(f'Dock return with status code: {response.code}')
        else:
            try:
                value = self.db.Get(tx_json['key'].encode('utf-8'))
            except Exception as exception:
                try:
                    with open(f"{self.db_path}/config/genesis.json") as file:
                        genesis = yaml.load(file, Loader=yaml.Loader)
                    chain_id = genesis['chain_id']
                    value = json.dumps({'value': tx_json['value'], 'keeper': {'app_id': tx_json['auth']['app_id'], 'chain_id': chain_id}})
                    self.db.Put(tx_json['key'].encode('utf-8'), value.encode('utf-8'))
                except Exception as exception:
                    log.error(repr(exception))
                    return types_pb2.ResponseDeliverTx(code=ErrorCode)
            try:
                value_json = json.loads(value)
                value_json['value'] = tx_json['value']
                value = json.dumps(value_json)
                self.db.Put(tx_json['key'].encode('utf-8'), value.encode('utf-8'))
            except Exception as exception:
                log.error(repr(exception))
                return types_pb2.ResponseDeliverTx(code=ErrorCode)
        return types_pb2.ResponseDeliverTx(code=OkCode)

    def query(self, req) -> types_pb2.ResponseQuery:
        req_json = json.loads(req.data.decode('utf-8'))
        if req_json.get('graph_data') is not None:
            try:
                with grpc.insecure_channel('localhost:1453') as channel:
                    log.info('Call dock grpc: UpdateGraphDta')
                    client = dci_pb2_grpc.DockStub(channel)
                    request = dci_pb2.RequestGetGraphData()
                    request.app_id.append(req_json['app_id'])
                    response = client.GetGraphData(request)
                    graph_data = [{'source_app_id': response.node_connections[index].source_app_id,
                                   'source_app_info': response.node_connections[index].source_app_info,
                                   'source_app_chain_id': response.node_connections[index].source_app_chain_id,
                                   'target_app_id': response.node_connections[index].target_app_id,
                                   'target_app_info': response.node_connections[index].target_app_info,
                                   'target_app_chain_id': response.node_connections[index].target_app_chain_id,
                                   'weight': response.node_connections[index].weight} for index in range(len(response.node_connections))]
                    return types_pb2.ResponseQuery(
                        code=OkCode, value=json.dumps(graph_data).encode('utf-8'), height=self.last_block_height
                    )
            except Exception as exception:
                log.error(repr(exception))
                return types_pb2.ResponseQuery(
                    code=ErrorCode, value=repr(exception).encode('utf-8'), height=self.last_block_height
                )
        else:
            try:
                value = self.db.Get(req_json['key'].encode('utf-8'))
                data_json = json.loads(bytes(value).decode('utf-8'))
                keeper = data_json['keeper']
                if req_json['auth']['app_id'] == self.app_id and req_json['auth']['app_id'] != keeper['app_id']:
                    request_update_graph_data = dci_pb2.RequestUpdateGraphData()
                    with open(f"{self.db_path}/config/genesis.json") as file:
                        genesis = yaml.load(file, Loader=yaml.Loader)
                    chain_id = genesis['chain_id']
                    request_update_graph_data.node_connections.append(dci_pb2.NodeConnection(source_app_id=self.app_id,
                                                                                             source_app_info='',
                                                                                             source_app_chain_id=chain_id,
                                                                                             target_app_id=keeper['app_id'],
                                                                                             target_app_info='',
                                                                                             target_app_chain_id=keeper['chain_id'],
                                                                                             weight=1))
                    with grpc.insecure_channel('localhost:1453') as channel:
                        log.info('Call dock grpc: UpdateGraphDta')
                        client = dci_pb2_grpc.DockStub(channel)
                        response = client.UpdateGraphData(request_update_graph_data)
                        log.info(f'Dock return with status code: {response.code}')
                return types_pb2.ResponseQuery(
                    code=OkCode, value=json.dumps(data_json['value']).encode('utf-8'), height=self.last_block_height
                )
            except Exception as exception:
                log.error(repr(exception))
                return types_pb2.ResponseQuery(
                    code=ErrorCode, value=repr(exception).encode('utf-8'), height=self.last_block_height
                )

    def commit(self) -> types_pb2.ResponseCommit:
        """Return the current encode state value to tendermint"""
        hash = struct.pack(">Q", self.last_block_height)
        return types_pb2.ResponseCommit(data=hash)

    def begin_block(self, req: types_pb2.RequestBeginBlock) -> types_pb2.ResponseBeginBlock:
        self.validator_updates = []
        return types_pb2.ResponseBeginBlock()

    def end_block(self, req: types_pb2.RequestEndBlock) -> types_pb2.ResponseEndBlock:
        return types_pb2.ResponseEndBlock(validator_updates=self.validator_updates)


def main(args):
    init_log()
    app = ABCIServer(app=IslandService(args[2], args[3]), port=args[1])
    app.run()


if __name__ == "__main__":
    main(sys.argv)
