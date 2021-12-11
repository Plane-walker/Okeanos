# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import dci_pb2 as dci_dot_dci__pb2


class DockStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.PackageTx = channel.unary_unary(
                '/dci.Dock/PackageTx',
                request_serializer=dci_dot_dci__pb2.RequestTxPackage.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseTxPackage.FromString,
                )
        self.RouterInfo = channel.unary_unary(
                '/dci.Dock/RouterInfo',
                request_serializer=dci_dot_dci__pb2.RequestRouterInfo.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.RequestRouterInfo.FromString,
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
        self.SwitchCommunity = channel.unary_unary(
                '/dci.Dock/SwitchCommunity',
                request_serializer=dci_dot_dci__pb2.RequestSwitchCommunity.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseSwitchCommunity.FromString,
                )
        self.CommunityInfo = channel.unary_unary(
                '/dci.Dock/CommunityInfo',
                request_serializer=dci_dot_dci__pb2.RequestCommunityInfo.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseCommunityInfo.FromString,
                )
        self.CommunityConfig = channel.unary_unary(
                '/dci.Dock/CommunityConfig',
                request_serializer=dci_dot_dci__pb2.RequestCommunityInfo.SerializeToString,
                response_deserializer=dci_dot_dci__pb2.ResponseCommunityInfo.FromString,
                )


class DockServicer(object):
    """Missing associated documentation comment in .proto file."""

    def PackageTx(self, request, context):
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

    def SwitchCommunity(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CommunityInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CommunityConfig(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DockServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'PackageTx': grpc.unary_unary_rpc_method_handler(
                    servicer.PackageTx,
                    request_deserializer=dci_dot_dci__pb2.RequestTxPackage.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseTxPackage.SerializeToString,
            ),
            'RouterInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.RouterInfo,
                    request_deserializer=dci_dot_dci__pb2.RequestRouterInfo.FromString,
                    response_serializer=dci_dot_dci__pb2.RequestRouterInfo.SerializeToString,
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
            'SwitchCommunity': grpc.unary_unary_rpc_method_handler(
                    servicer.SwitchCommunity,
                    request_deserializer=dci_dot_dci__pb2.RequestSwitchCommunity.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseSwitchCommunity.SerializeToString,
            ),
            'CommunityInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.CommunityInfo,
                    request_deserializer=dci_dot_dci__pb2.RequestCommunityInfo.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseCommunityInfo.SerializeToString,
            ),
            'CommunityConfig': grpc.unary_unary_rpc_method_handler(
                    servicer.CommunityConfig,
                    request_deserializer=dci_dot_dci__pb2.RequestCommunityInfo.FromString,
                    response_serializer=dci_dot_dci__pb2.ResponseCommunityInfo.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dci.Dock', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Dock(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def PackageTx(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/PackageTx',
            dci_dot_dci__pb2.RequestTxPackage.SerializeToString,
            dci_dot_dci__pb2.ResponseTxPackage.FromString,
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
            dci_dot_dci__pb2.RequestRouterInfo.FromString,
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
    def SwitchCommunity(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/SwitchCommunity',
            dci_dot_dci__pb2.RequestSwitchCommunity.SerializeToString,
            dci_dot_dci__pb2.ResponseSwitchCommunity.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CommunityInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/CommunityInfo',
            dci_dot_dci__pb2.RequestCommunityInfo.SerializeToString,
            dci_dot_dci__pb2.ResponseCommunityInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CommunityConfig(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dci.Dock/CommunityConfig',
            dci_dot_dci__pb2.RequestCommunityInfo.SerializeToString,
            dci_dot_dci__pb2.ResponseCommunityInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
