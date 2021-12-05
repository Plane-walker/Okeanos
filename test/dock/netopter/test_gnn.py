import unittest
from dock.netopter import NetworkOptimizer


class TestNodeClassification(unittest.TestCase):
    def test_switch_community(self):
        self.assertEqual(NetworkOptimizer, 1)


if __name__ == '__main__':
    unittest.main()
