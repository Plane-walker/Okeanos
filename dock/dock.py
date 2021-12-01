from dock.interface.dci_pb2 import RouterChain


def test():
    re = RouterChain(identifier=1)
    print(re.identifier)
