__all__ = [
    'CrossChainCommunicationProtocol'
]

from concurrent import futures
import grpc
import time
from interface.dci import dci_pb2_grpc, dci_pb2


class CrossChainCommunicationProtocol(dci_pb2_grpc.DockServicer):

    # @staticmethod
    # def response_message(self):
    #     return dci_pb2.ResponseMessage(message="Interface call succeeded")

    @staticmethod
    def get_target_id(self, request_tx_passage, context):
        print(request_tx_passage)
        dci_pb2.ResponseMessage(message="Interface call succeeded")
        target_id = request_tx_passage.target_id
        print(target_id)
        return target_id

    # In order to test, the server code is written
    @staticmethod
    def serve(self):
        # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        dci_pb2_grpc.add_DockServicer_to_server(CrossChainCommunicationProtocol(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        print("start succeed")
        try:
            while True:
                time.sleep(60 * 60 * 24)
        except KeyboardInterrupt:
            server.stop(0)

    if __name__ == '__main__':
        serve()
