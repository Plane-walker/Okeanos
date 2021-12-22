import unittest
import uuid
from dock.router.router import Router
from interface.dci.dci_pb2 import (
    Chain,
)


class TestRouter(unittest.TestCase):
    
    def test_next_node(self):
        router = Router()
        ids = []
        TEST_NUM = 5
        for _ in range(TEST_NUM):
            identifier = uuid.uuid4().fields[0]
            router.paths[identifier] = Chain(identifier=identifier)
            ids.append(identifier)
        for id in ids:
            self.assertTrue(id in router.paths)
            self.assertEqual(id, router.next_node(Chain(identifier=id)).identifier)
        for _ in range(TEST_NUM):
            self.assertIsNone(router.next_node(Chain(identifier=uuid.uuid4().fields[0])))


if __name__ == '__main__':
    unittest.main()
