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
import leveldb
from log import init_log, log
from interface.dci import dci_pb2_grpc, dci_pb2
from interface.common import id_pb2

from interface.sci.abci.types_pb2 import (
    ResponseInfo,
    ResponseInitChain,
    ResponseCheckTx,
    ResponseDeliverTx,
    ResponseQuery,
    ResponseCommit,
)

from base.server import ABCIServer
from base.application import BaseApplication, OkCode


def encode_number(value):
    return struct.pack(">I", value)


def decode_number(raw):
    return int.from_bytes(raw, byteorder="big")


class IslandService(BaseApplication):
    def __init__(self, db_path):
        self.db = leveldb.LevelDB(os.path.join(db_path, 'db'))
        self.last_block_height = None

    def info(self, req) -> ResponseInfo:
        """
        Since this will always respond with height=0, Tendermint
        will resync this app from the beginning
        """
        r = ResponseInfo()
        r.version = req.version
        r.last_block_height = 0
        r.last_block_app_hash = b""
        return r

    def init_chain(self, req) -> ResponseInitChain:
        """Set initial state on first run"""
        self.last_block_height = 0
        return ResponseInitChain()

    def check_tx(self, tx) -> ResponseCheckTx:
        return ResponseCheckTx(code=OkCode)

    def deliver_tx(self, tx) -> ResponseDeliverTx:
        tx_json = json.loads(tx.decode('utf-8'))
        if tx_json.get('target') is not None:
            request_tx_package = dci_pb2.RequestDeliverTx(
                tx=tx,
                target=id_pb2.Chain(identifier=tx_json['target']),
                source=id_pb2.Chain(identifier=tx_json['source']),
                flag=tx_json['flag']
            )
            with grpc.insecure_channel('localhost:1453') as channel:
                log.info('Call dock grpc : PackageTx')
                client = dci_pb2_grpc.DockStub(channel)
                response = next(client.DeliverTx(request_tx_package))
                log.info(f'Dock return with status code: {response.code}')
        else:
            self.db.Put(tx_json['user_id'].encode('utf-8'), tx_json['user_data'].encode('utf-8'))
        return ResponseDeliverTx(code=OkCode)

    def query(self, req) -> ResponseQuery:
        value = self.db.Get(req.data)
        return ResponseQuery(
            code=OkCode, value=bytes(value), height=self.last_block_height
        )

    def commit(self) -> ResponseCommit:
        """Return the current encode state value to tendermint"""
        hash = struct.pack(">Q", self.last_block_height)
        return ResponseCommit(data=hash)


def main(args):
    init_log()
    app = ABCIServer(app=IslandService(args[2]), port=args[1])
    app.run()


if __name__ == "__main__":
    main(sys.argv)
