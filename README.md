# Okeanos
 A Self-regulating Multi-blockchain Interconnection Architecture

## Dependencies
* Python == 3.8
* protobuf == 3.17.2
* grpcio == 1.42.0
* grpcio-tools == 1.42.0
* pyyaml == 6.0
* tensorflow == 2.3.0
* numpy == 1.21.2
* scikit-learn == 1.0.1
* networkx == 2.6.3
* pandas == 1.3.4
* requests == 2.26.0

## Start a single node
Use Ubuntu == 20.04

Copy the source code to /root

```
cd Okenaos
python main.py
```

## Start multi-nodes with multi-blockchains
Use Ubuntu == 20.04

Copy the source code to /root

Within every node, run: 
```
cd Okenaos
mkdir config
cp dock/config/default_config.yaml config/dock.yaml
```

Edit the dock.yaml for every node, then run the following command in every node:
```
python main.py
```

Refer to the test/ for more details.

There are also some scripts in test/multi_host providing a faster way to create a 33 nodes network and test the RPS and response time on it.

## Build/Rebuild protobuf files
```
cd protos
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. gogoproto/*.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. dci/*.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. bci/*.proto
```

## Message format
```
{
  'header':
  {
    'type': enum{'write', 'cross_write', 'read', 'cross_read', 'graph', 'cross_graph', 'route', 'validate', 'join', 'switch'},
    'ttl': int(default: -1),
    'paths': array[string](default: []),
    'source_chain_id': string(defalut: ''),
    'target_chain_id': string(defalut: ''),
    'auth': {'app_id': string(defalut: ''), 'app_info': string(defalut: '')},
    'timestamp': time.time(),
  }
  'body': {'key': (string), 'value': (string)/ 'public_key': (string), 'power': (int)/'app_id': (string)}
}
```
