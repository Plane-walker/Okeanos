from __future__ import print_function
import tensorflow as tf
from tensorflow.keras.layers import Activation, Layer, Concatenate, Average, Reshape
from typing import AnyStr, Optional


def sample_features(origin_nodes, sample_sizes, adjacency_matrix, features):
    sample_result = [[[nodes] for nodes in origin_nodes]]
    sample_features_result = [np.array(features[origin_nodes]).reshape(-1, 1, features.shape[1])]
    for index in range(len(sample_sizes)):
        neighbor_nodes = []
        neighbor_nodes_features = []
        for origin_nodes in sample_result[index]:
            neighbor_node = []
            neighbor_node_features = []
            for origin_node in origin_nodes:
                nonzero_neighbor_nodes = np.array(np.nonzero(adjacency_matrix[origin_node])).reshape(-1)
                neighbor_node.extend(np.random.choice(nonzero_neighbor_nodes, size=(sample_sizes[index], )))
                neighbor_node_features.extend(features[np.random.choice(nonzero_neighbor_nodes, size=(sample_sizes[index], ))])
            neighbor_nodes.append(neighbor_node)
            neighbor_nodes_features.append(neighbor_node_features)
        sample_result.append(neighbor_nodes)
        sample_features_result.append(np.array(neighbor_nodes_features))
    return sample_features_result


def sample_features_unsupervised(origin_nodes, sample_sizes, adjacency_matrix, features):
    src_nodes, dst_nodes = zip(*origin_nodes)
    src_features = sample_features(list(src_nodes), sample_sizes, adjacency_matrix, features)
    dst_features = sample_features(list(dst_nodes), sample_sizes, adjacency_matrix, features)
    sample_features_result = [feature for pair in zip(src_features, dst_features) for feature in pair]
    return sample_features_result


class LinkEmbedding(Layer):
    """
    Defines an edge inference function that takes source, destination node embeddings
    (node features) as input, and returns a numeric vector of output_dim size.
    This class takes as input as either:
     * A list of two tensors of shape (N, M) being the embeddings for each of the nodes in the link,
       where N is the number of links, and M is the node embedding size.
     * A single tensor of shape (..., N, 2, M) where the axis second from last indexes the nodes
       in the link and N is the number of links and M the embedding size.
    Examples:
        Consider two tensors containing the source and destination embeddings of size M::
            x_src = tf.constant(x_src, shape=(1, M), dtype="float32")
            x_dst = tf.constant(x_dst, shape=(1, M), dtype="float32")
            li = LinkEmbedding(method="ip", activation="sigmoid")([x_src, x_dst])
    .. seealso::
       Examples using this class:
       - `GCN link prediction <https://stellargraph.readthedocs.io/en/stable/demos/link-prediction/gcn-link-prediction.html>`__
       - `comparison of link prediction algorithms <https://stellargraph.readthedocs.io/en/stable/demos/link-prediction/homogeneous-comparison-link-prediction.html>`__
       Related functions: :func:`.link_inference`, :func:`.link_classification`, :func:`.link_regression`.
    Args:
        axis (int): If a single tensor is supplied this is the axis that indexes the node
            embeddings so that the indices 0 and 1 give the node embeddings to be combined.
            This is ignored if two tensors are supplied as a list.
        activation (str), optional: activation function applied to the output, one of "softmax", "sigmoid", etc.,
            or any activation function supported by Keras, see https://keras.io/activations/ for more information.
        method (str), optional: Name of the method of combining ``(src,dst)`` node features or embeddings into edge embeddings.
            One of:
            * ``concat`` -- concatenation,
            * ``ip`` or ``dot`` -- inner product, :math:`ip(u,v) = sum_{i=1..d}{u_i*v_i}`,
            * ``mul`` or ``hadamard`` -- element-wise multiplication, :math:`h(u,v)_i = u_i*v_i`,
            * ``l1`` -- L1 operator, :math:`l_1(u,v)_i = |u_i-v_i|`,
            * ``l2`` -- L2 operator, :math:`l_2(u,v)_i = (u_i-v_i)^2`,
            * ``avg`` -- average, :math:`avg(u,v) = (u+v)/2`.
            For all methods except ``ip`` or ``dot`` a dense layer is applied on top of the combined
            edge embedding to transform to a vector of size ``output_dim``.
    """

    def __init__(
            self,
            method: AnyStr = "ip",
            axis: Optional[int] = -2,
            activation: Optional[AnyStr] = "linear",
            **kwargs
    ):
        super().__init__(**kwargs)
        self.method = method.lower()
        self.axis = axis
        self.activation = tf.keras.activations.get(activation)

    def get_config(self):
        config = {
            "activation": tf.keras.activations.serialize(self.activation),
            "method": self.method,
            "axis": self.axis,
        }
        base_config = super().get_config()
        return dict(list(base_config.items()) + list(config.items()))

    def call(self, x, **kwargs):
        """
        Apply the layer to the node embeddings in x. These embeddings are either:
          * A list of two tensors of shape (N, M) being the embeddings for each of the nodes in the link,
            where N is the number of links, and M is the node embedding size.
          * A single tensor of shape (..., N, 2, M) where the axis second from last indexes the nodes
            in the link and N is the number of links and M the embedding size.
        """
        # Currently GraphSAGE & HinSage output a list of two tensors being the embeddings
        # for each of the nodes in the link. However, GCN, GAT & other full-batch methods
        # return a tensor of shape (1, N, 2, M).
        # Detect and support both inputs
        if isinstance(x, (list, tuple)):
            if len(x) != 2:
                raise ValueError("Expecting a list of length 2 for link embedding")
            x0, x1 = x
        elif isinstance(x, tf.Tensor):
            if int(x.shape[self.axis]) != 2:
                raise ValueError(
                    "Expecting a tensor of shape 2 along specified axis for link embedding"
                )
            x0, x1 = tf.unstack(x, axis=self.axis)
        else:
            raise TypeError("Expected a list, tuple, or Tensor as input")

        # Apply different ways to combine the node embeddings to a link embedding.
        if self.method in ["ip", "dot"]:
            out = tf.reduce_sum(x0 * x1, axis=-1, keepdims=True)

        elif self.method == "l1":
            # l1(u,v)_i = |u_i - v_i| - vector of the same size as u,v
            out = tf.abs(x0 - x1)

        elif self.method == "l2":
            # l2(u,v)_i = (u_i - v_i)^2 - vector of the same size as u,v
            out = tf.square(x0 - x1)

        elif self.method in ["mul", "hadamard"]:
            out = tf.multiply(x0, x1)

        elif self.method == "concat":
            out = Concatenate()([x0, x1])

        elif self.method == "avg":
            out = Average()([x0, x1])

        else:
            raise NotImplementedError(
                "{}: the requested method '{}' is not known/not implemented"
            )

        # Apply activation function
        out = self.activation(out)

        return out


def link_classification(output_dim, output_act, edge_embedding_method):
    def edge_function(x):
        le = LinkEmbedding(activation="linear", method=edge_embedding_method)(x)

        # All methods apart from inner product have a dense layer
        # to convert link embedding to the desired output
        out = Activation(output_act)(le)
        # Reshape outputs
        out = Reshape((output_dim,))(out)
        return out
    return edge_function
