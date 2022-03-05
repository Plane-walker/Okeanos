"""
Simple counting app.  It only accepts values sent to it in correct order.  The
state maintains the current count. For example, if starting at state 0, sending:
-> 0x01 = OK
-> 0x03 = Will fail! (expects 2)

To run it:
- make a clean new directory for tendermint
- start this server: python counter.py
- start tendermint: tendermint --home "YOUR DIR HERE" node
- The send transactions to the app:


curl http://localhost:2663/broadcast_tx_commit?tx=0x01
curl http://localhost:2663/broadcast_tx_commit?tx=0x02
...

To see the latest count:
curl http://localhost:2663/abci_query

The way the app state is structured, you can also see the current state value
in the tendermint console output (see app_hash).
"""
import os
import leveldb
import json
import struct
import sys
import grpc
import base64
import hashlib
import yaml

from log import init_log, log
from interface.dci import dci_pb2_grpc, dci_pb2
from interface.common import id_pb2
from interface.sci.abci import types_pb2
from interface.sci.crypto import keys_pb2

from base.server import ABCIServer
from base.application import BaseApplication, OkCode, ErrorCode


# Tx encoding/decoding


def encode_number(value):
    return struct.pack(">I", value)


def decode_number(raw):
    return int.from_bytes(raw, byteorder="big")


class LaneService(BaseApplication):
    def __init__(self, node_id, db_path):
        self.node_id = node_id
        self.db = leveldb.LevelDB(os.path.join(db_path, 'db'))
        self.last_block_height = None
        self.validator_updates = []
        self.address_to_public_key = {}

    def info(self, req) -> types_pb2.ResponseInfo:
        """
        Since this will always respond with height=0, Tendermint
        will resync this app from the begining
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
            log.info(f'Check for tx {tx_json}')
        except Exception as exception:
            log.error(repr(exception), data=repr(exception).encode('utf-8'))
        return types_pb2.ResponseCheckTx(code=OkCode)

    def deliver_tx(self, tx) -> types_pb2.ResponseDeliverTx:
        try:
            tx_json = json.loads(tx.decode('utf-8'))
            log.info(f'Received tx {tx_json}')
            message_type = tx_json['header']['type']
            if message_type == 'normal':
                key = tx_json['body']['key'].encode('utf-8')
                try:
                    value = self.db.Get(key)
                except Exception as exception:
                    log.info(repr(exception))
                    with open(f"{self.db_path}/config/genesis.json") as file:
                        genesis = yaml.load(file, Loader=yaml.Loader)
                    chain_id = genesis['chain_id']
                    value = json.dumps({
                        'value': tx_json['body']['value'],
                        'keeper': {
                            'app_id': tx_json['header']['auth']['app_id'],
                            'chain_id': chain_id
                        }
                    })
                    self.db.Put(key, value.encode('utf-8'))
                    return types_pb2.ResponseDeliverTx(code=OkCode)
                value_json = json.loads(value.decode('utf-8'))
                value_json['value'] = tx_json['body']['value']
                value = json.dumps(value_json)
                self.db.Put(key, value.encode('utf-8'))
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'validate':
                validator_update = types_pb2.ValidatorUpdate(
                    pub_key=keys_pb2.PublicKey(ed25519=base64.b64decode(tx_json['body']['public_key'])),
                    power=tx_json['body']['power'])
                self.update_validator(validator_update)
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'route':
                request_tx_package = dci_pb2.RequestDeliverTx(tx=tx)
                with grpc.insecure_channel('localhost:1453') as channel:
                    log.info(f'Call dock DeliverTx with {message_type} type with {tx_json}.')
                    client = dci_pb2_grpc.DockStub(channel)
                    log.warning(f'client {repr(client)}')
                    response = next(client.DeliverTx(request_tx_package))
                    log.info(f'Dock return with status code: {response.code} for {tx_json}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'cross':
                request_tx_package = dci_pb2.RequestDeliverTx(
                    tx=tx,
                    target=id_pb2.Chain(identifier=tx_json['header']['target_chain_id']),
                    source=id_pb2.Chain(identifier=tx_json['header']['source_chain_id']),
                    )
                with grpc.insecure_channel('localhost:1453') as channel:
                    log.info(f'Call dock DeliverTx with {message_type} type with {tx_json}.')
                    client = dci_pb2_grpc.DockStub(channel)
                    log.warning(f'client {repr(client)}')
                    response = next(client.DeliverTx(request_tx_package))
                    log.info(f'Dock return with status code: {response.code} for {tx_json}')
                return types_pb2.ResponseDeliverTx(code=OkCode)
            elif message_type == 'graph':
                log.warning(f'Received graph message: {tx_json}')
            else:
                raise ValueError('type of message is not supported')
            return types_pb2.ResponseDeliverTx(code=OkCode)
        except Exception as exception:
            log.error(repr(exception))
            return types_pb2.ResponseDeliverTx(
                code=ErrorCode, data=repr(exception).encode('utf-8')
            )
        # tx_json = json.loads(tx.decode('utf-8'))
        # log.warning('tx_json: %s', tx_json)
        # if tx_json.get('validator') is not None:
        #     validator_update = types_pb2.ValidatorUpdate(pub_key=keys_pb2.PublicKey(ed25519=base64.b64decode(tx_json['validator']['public_key'])),
        #                                                  power=tx_json['validator']['power'])
        #     self.update_validator(validator_update)
        # elif tx_json.get('target') is not None:
        #     try:
        #         request_tx_package = dci_pb2.RequestDeliverTx(
        #             tx=tx,
        #             target=id_pb2.Chain(identifier=tx_json['target']),
        #             source=id_pb2.Chain(identifier=tx_json['source']),
        #             type=tx_json.get('type')
        #         )
        #         if tx_json.get('ttl') is not None:
        #             request_tx_package.ttl = tx_json['ttl']
        #         if tx_json.get('paths') is not None:
        #             request_tx_package.paths.extend([id_pb2.Chain(identifier=path) for path in tx_json['paths']])
        #         with grpc.insecure_channel('localhost:1453') as channel:
        #             log.info('Call dock grpc: DeliverTx')
        #             client = dci_pb2_grpc.DockStub(channel)
        #             response = next(client.DeliverTx(request_tx_package))
        #             log.info(f'Dock return with status code: {response.code}')
        #     except Exception as exception:
        #         log.error(repr(exception))
        #         return types_pb2.ResponseDeliverTx(code=ErrorCode)
        # else:
        #     try:
        #         self.db.Put(tx_json['key'].encode('utf-8'), tx_json['value'].encode('utf-8'))
        #     except Exception as exception:
        #         log.error(repr(exception))
        #         return types_pb2.ResponseDeliverTx(code=ErrorCode)
        # return types_pb2.ResponseDeliverTx(code=OkCode)

    def query(self, req) -> types_pb2.ResponseQuery:
        try:
            value = self.db.Get(req.data)
        except Exception as exception:
            log.error(repr(exception))
            return types_pb2.ResponseQuery(
                code=ErrorCode, value=repr(exception).encode('utf-8'), height=self.last_block_height
            )
        return types_pb2.ResponseQuery(
            code=OkCode, value=bytes(value), height=self.last_block_height
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
    app = ABCIServer(app=LaneService(args[2], args[3]), port=args[1])
    app.run()


if __name__ == "__main__":
    main(sys.argv)
