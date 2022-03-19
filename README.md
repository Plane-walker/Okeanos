# Okeanos
Multi-chain based IoT network

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
    'type': (string/'normal', 'cross_write', 'cross_query', 'cross_graph', 'route', 'validate', 'graph'),
    'ttl': (int/-1),
    'paths': (array(string)/),
    'source_chain_id': (string),
    'target_chain_id': (string),
    'auth': {'app_id': (string)}
  }
  'body': {'key': (string), 'value': (string)/ 'public_key': (string), 'power': (int)/'query': (string)}
}
```
