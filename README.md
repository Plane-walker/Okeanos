# Okeanos
Multi-chain based IoT network

## Dependencies
* Python == 3.8
* protobuf == 3.17.2
* grpcio == 1.42.0
* grpc-tools == 1.42.0
* pyyaml == 6.0
* tensorflow == 2.3.0
* numpy == 1.21.2

## Build/Rebuild protobuf files
```
cd protos
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. gogoproto/*.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. dci/*.proto
```
