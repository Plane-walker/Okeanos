__all__ = [
    'CrossChainCommunicationProtocol'
]


class CrossChainCommunicationProtocol:

    def __init__(self, router):
        self.next_router_path = None
        self.targetID = None
        self.data = {'target_id': '1234', 'node_id': '2345'}
        self.router = router

    def get_target_id(self, request_tx_passage):
        target_id = request_tx_passage.get('target_id')
        self.targetID = target_id
        return target_id

    def query_route_path(self):
        self.next_router_path = self.router.next_node(self.targetID)
    