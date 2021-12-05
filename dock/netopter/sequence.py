__all__ = [
    'NodeSequence',
    'OnDemandLinkSequence'
]


import collections
import numpy as np
from tensorflow.keras.utils import Sequence
from .random_walker import UniformRandomWalk


class NodeSequence(Sequence):
    """Keras-compatible data generator to use with the Keras
    methods :meth:`keras.Model.fit`, :meth:`keras.Model.evaluate`,
    and :meth:`keras.Model.predict`.
    This class generated data samples for node inference models
    and should be created using the `.flow(...)` method of
    :class:`.GraphSAGENodeGenerator` or :class:`.DirectedGraphSAGENodeGenerator`
    or :class:`.HinSAGENodeGenerator` or :class:`.Attri2VecNodeGenerator`.
    These generator classes are used within the NodeSequence to generate
    the required features for downstream ML tasks from the graph.
    Args:
        sample_function (Callable): A function that returns features for supplied head nodes.
        ids (list): A list of the node_ids to be used as head-nodes in the downstream task.
        targets (list, optional): A list of targets or labels to be used in the downstream task.
        shuffle (bool): If True (default) the ids will be randomly shuffled every epoch.
    """

    def __init__(
            self, sample_function, batch_size, ids, adjacency_matrix, features, sample_sizes, targets=None, shuffle=True
    ):
        # Check targets is iterable & has the correct length
        if targets is not None:
            if len(ids) != len(targets):
                raise ValueError(
                    "The length of the targets must be the same as the length of the ids"
                )
            self.targets = np.asanyarray(targets)
        else:
            self.targets = None

        # Store the generator to draw samples from graph
        if isinstance(sample_function, collections.abc.Callable):
            self._sample_function = sample_function
        else:
            raise TypeError(
                "({}) The sampling function expects a callable function.".format(
                    type(self).__name__
                )
            )

        self.ids = list(ids)
        self.data_size = len(self.ids)
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.adjacency_matrix = adjacency_matrix
        self.features = features
        self.sample_sizes = sample_sizes
        self.indices = list(range(self.data_size))

    def __len__(self):
        """Denotes the number of batches per epoch"""
        return int(np.ceil(self.data_size / self.batch_size))

    def __getitem__(self, batch_num):
        """
        Generate one batch of data
        Args:
            batch_num (int): number of a batch
        Returns:
            batch_feats (list): Node features for nodes and neighbours sampled from a
                batch of the supplied IDs
            batch_targets (list): Targets/labels for the batch.
        """
        start_idx = self.batch_size * batch_num
        end_idx = start_idx + self.batch_size
        if start_idx >= self.data_size:
            raise IndexError("Mapper: batch_num larger than length of data")
        # print("Fetching batch {} [{}]".format(batch_num, start_idx))

        # The ID indices for this batch
        batch_indices = self.indices[start_idx:end_idx]

        # Get head (root) nodes
        head_ids = [self.ids[ii] for ii in batch_indices]

        # Get corresponding targets
        batch_targets = None if self.targets is None else self.targets[batch_indices]

        # Get features for nodes
        batch_feats = self._sample_function(head_ids, self.sample_sizes, self.adjacency_matrix, self.features)
        return batch_feats, batch_targets


class OnDemandLinkSequence(Sequence):
    """
    Keras-compatible data generator to use with Keras methods :meth:`keras.Model.fit`,
    :meth:`keras.Model.evaluate`, and :meth:`keras.Model.predict`
    This class generates data samples for link inference models
    and should be created using the :meth:`flow` method of
    :class:`.GraphSAGELinkGenerator` or :class:`.Attri2VecLinkGenerator`.
    Args:
        sample_function (Callable): A function that returns features for supplied head nodes.
        sampler (UnsupersizedSampler):  An object that encapsulates the neighbourhood sampling of a graph.
            The generator method of this class returns a batch of positive and negative samples on demand.
    """

    def __init__(self, sample_function, batch_size, adjacency_matrix, features, sample_sizes, shuffle=True):
        # Store the generator to draw samples from graph
        if isinstance(sample_function, collections.abc.Callable):
            self._sample_features = sample_function
        else:
            raise TypeError(
                "({}) The sampling function expects a callable function.".format(
                    type(self).__name__
                )
            )

        self.batch_size = batch_size
        self.adjacency_matrix = adjacency_matrix
        self.features = features
        self.sample_sizes = sample_sizes
        self.shuffle = shuffle
        self._batches = self._create_batches(batch_size)
        self.length = len(self._batches)

    def __getitem__(self, batch_num):
        """
        Generate one batch of data.
        Args:
            batch_num<int>: number of a batch
        Returns:
            batch_feats<list>: Node features for nodes and neighbours sampled from a
                batch of the supplied IDs
            batch_targets<list>: Targets/labels for the batch.
        """

        if batch_num >= self.__len__():
            raise IndexError(
                "Mapper: batch_num larger than number of esstaimted  batches for this epoch."
            )
        # print("Fetching {} batch {} [{}]".format(self.name, batch_num, start_idx))

        # Get head nodes and labels
        head_ids, batch_targets = self._batches[batch_num]

        # Obtain features for head ids
        batch_feats = self._sample_features(head_ids, self.sample_sizes, self.adjacency_matrix, self.features)
        return batch_feats, batch_targets

    def __len__(self):
        """Denotes the number of batches per epoch"""
        return self.length

    def _create_batches(self, batch_size):
        self.walker = UniformRandomWalk(self.adjacency_matrix, 1, 5)
        nodes = np.arange(0, self.adjacency_matrix.shape[0])
        degrees = np.sum(self.adjacency_matrix, axis=1).reshape(-1)
        sampling_distribution = np.array([degrees[n] ** 0.75 for n in nodes])
        sampling_distribution_norm = sampling_distribution / np.sum(
            sampling_distribution
        )
        walks = self.walker.run(nodes)
        targets = [walk[0] for walk in walks]

        positive_pairs = np.array(
            [
                (target, positive_context)
                for target, walk in zip(targets, walks)
                for positive_context in walk[1:]
            ]
        )
        negative_samples = np.random.choice(
            nodes, size=len(positive_pairs), p=sampling_distribution_norm
        )
        negative_pairs = np.column_stack((positive_pairs[:, 0], negative_samples))
        pairs = np.concatenate((positive_pairs, negative_pairs), axis=0)
        labels = np.repeat([1, 0], len(positive_pairs))
        indices = np.random.permutation(len(pairs))
        batch_indices = [
            indices[i: i + batch_size] for i in range(0, len(indices), batch_size)
        ]
        return [(pairs[i], labels[i]) for i in batch_indices]
