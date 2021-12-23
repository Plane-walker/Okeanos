from concurrent import futures
from interface.dci.dci_pb2_grpc import DockServicer as Servicer
from interface.dci.dci_pb2_grpc import add_DockServicer_to_server
from router.router import Router
from interface.dci.dci_pb2 import ResponseRouterInfo
import grpc
import time


class DockServicer(Servicer):
    
    def __init__(self) -> None:
        self.router = Router()
    
    def RouterInfo(self, request, context):
        print(request)
        res = self.router.info(request)
        print(res)
        return res
    
    def RouterTransmit(self, request, context):
        return self.router.transmit(request)
    
    def RouterPathCallback(self, request, context):
        return self.router.callback(request)


ONE_DAY_IN_SECONDS = 60 * 60 * 24
HOST = 'localhost'
PORT = '5000'

def run():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_DockServicer_to_server(DockServicer(), server)
    print(f'"msg":"grpc start @ grpc://{HOST}:{PORT}"')
    server.add_insecure_port(f"{HOST}:{PORT}")
    server.start()
    # server.wait_for_termination()
    try:
        while True:
            time.sleep(ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
    except Exception as e:
        server.stop(0)
        raise


if __name__ == '__main__':
    run()
