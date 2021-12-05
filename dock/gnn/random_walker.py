from abc import ABC, abstractmethod
import numpy as np


class RandomWalk(ABC):
    """
    Abstract base class for Random Walk classes. A Random Walk class must implement a ``run`` method
    which takes an iterable of node IDs and returns a list of walks. Each walk is a list of node IDs
    that contains the starting node as its first element.
    """

    def __init__(self, adjacency_matrix, seed=None):
        self.adjacency_matrix = adjacency_matrix
        self.seed = seed

    @abstractmethod
    def run(self, nodes, **kwargs):
        pass


class UniformRandomWalk(RandomWalk):
    """
    Performs uniform random walks on the given graph
    .. seealso::
       Related functionality:
       - :class:`.UnsupervisedSampler` for transforming random walks into links for unsupervised training of link prediction models
       - Other random walks: :class:`.BiasedRandomWalk`, :class:`.UniformRandomMetaPathWalk`, :class:`.TemporalRandomWalk`.
    Args:
        graph (StellarGraph): Graph to traverse
        n (int, optional): Total number of random walks per root node
        length (int, optional): Maximum length of each random walk
        seed (int, optional): Random number generator seed
    """

    def __init__(self, adjacency_matrix, n=None, length=None, seed=None):
        super().__init__(adjacency_matrix, seed=seed)
        self.n = n
        self.length = length

    def run(self, nodes, *, n=None, length=None, seed=None):
        """
        Perform a random walk starting from the root nodes. Optional parameters default to using the
        values passed in during construction.
        Args:
            nodes (list): The root nodes as a list of node IDs
            n (int, optional): Total number of random walks per root node
            length (int, optional): Maximum length of each random walk
            seed (int, optional): Random number generator seed
        Returns:
            List of lists of nodes ids for each of the random walks
        """
        # for each root node, do n walks
        return [self._walk(node, self.length) for node in nodes for _ in range(self.n)]

    def _walk(self, start_node, length):
        walk = [start_node]
        current_node = start_node
        for _ in range(length - 1):
            neighbours = np.array(np.nonzero(self.adjacency_matrix[current_node])).reshape(-1)
            if len(neighbours) == 0:
                # dead end, so stop
                break
            else:
                # has neighbours, so pick one to walk to
                current_node = np.random.choice(neighbours)
            walk.append(current_node)

        return walk
