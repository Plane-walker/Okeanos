# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import interface.dci.dci_pb2 as dci_dot_dci__pb2


class DockStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.DeliverTx = channel.unary_unary(
                '/dci.Dock/DeliverTx',
                request_serializer=dci_dot_dci__pb2.RequestDeliverTx.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseDeliverTx.FromString,
                )
        self.RouterInfo = channel.unary_unary(
                '/dci.Dock/RouterInfo',
                request_serializer=dci_dot_dci__pb2.RequestRouterInfo.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseRouterInfo.FromString,
                )
        self.RouterTransmit = channel.unary_unary(
                '/dci.Dock/RouterTransmit',
                request_serializer=dci_dot_dci__pb2.RequestRouterTransmit.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseRouterTransmit.FromString,
                )
        self.RouterPathCallback = channel.unary_unary(
                '/dci.Dock/RouterPathCallback',
                request_serializer=dci_dot_dci__pb2.RequestRouterPathCallback.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseRouterPathCallback.FromString,
                )
        self.Shard = channel.unary_unary(
                '/dci.Dock/Shard',
                request_serializer=dci_dot_dci__pb2.RequestShard.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseShard.FromString,
                )
        self.Switch = channel.unary_unary(
                '/dci.Dock/Switch',
                request_serializer=dci_dot_dci__pb2.RequestSwitch.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseSwitch.FromString,
                )


class DockServicer(object):
    """Missing associated documentation comment in .proto file."""

    def DeliverTx(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RouterInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RouterTransmit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RouterPathCallback(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Shard(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Switch(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DockServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'DeliverTx': grpc.unary_unary_rpc_method_handler(
                    servicer.DeliverTx,
                    request_deserializer=dci_dot_dci__pb2.RequestDeliverTx.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseDeliverTx.SerializeToString,
            ),
            'RouterInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.RouterInfo,
                    request_deserializer=dci_dot_dci__pb2.RequestRouterInfo.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseRouterInfo.SerializeToString,
            ),
            'RouterTransmit': grpc.unary_unary_rpc_method_handler(
                    servicer.RouterTransmit,
                    request_deserializer=dci_dot_dci__pb2.RequestRouterTransmit.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseRouterTransmit.SerializeToString,
            ),
            'RouterPathCallback': grpc.unary_unary_rpc_method_handler(
                    servicer.RouterPathCallback,
                    request_deserializer=dci_dot_dci__pb2.RequestRouterPathCallback.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseRouterPathCallback.SerializeToString,
            ),
            'Shard': grpc.unary_unary_rpc_method_handler(
                    servicer.Shard,
                    request_deserializer=dci_dot_dci__pb2.RequestShard.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseShard.SerializeToString,
            ),
            'Switch': grpc.unary_unary_rpc_method_handler(
                    servicer.Switch,
                    request_deserializer=dci_dot_dci__pb2.RequestSwitch.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseSwitch.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dci.Dock', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Dock(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def DeliverTx(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/DeliverTx',
            dci_dot_dci__pb2.RequestDeliverTx.SerializeToString,
            dci_dot_dci__pb2.ResponseDeliverTx.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RouterInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/RouterInfo',
            dci_dot_dci__pb2.RequestRouterInfo.SerializeToString,
            dci_dot_dci__pb2.ResponseRouterInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RouterTransmit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/RouterTransmit',
            dci_dot_dci__pb2.RequestRouterTransmit.SerializeToString,
            dci_dot_dci__pb2.ResponseRouterTransmit.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RouterPathCallback(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/RouterPathCallback',
            dci_dot_dci__pb2.RequestRouterPathCallback.SerializeToString,
            dci_dot_dci__pb2.ResponseRouterPathCallback.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Shard(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/Shard',
            dci_dot_dci__pb2.RequestShard.SerializeToString,
            dci_dot_dci__pb2.ResponseShard.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Switch(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/Switch',
            dci_dot_dci__pb2.RequestSwitch.SerializeToString,
            dci_dot_dci__pb2.ResponseSwitch.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
