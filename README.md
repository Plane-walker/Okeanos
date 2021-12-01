# Okeanos
Multi-chain based IoT network

## build/rebuild protobuf files
```
cd protos
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. gogoproto/*.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. dci/*.proto
```
