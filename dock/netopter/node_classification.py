__all__ = [
    'NodeClassificationModel',
    'GraphSAGEModel'
]

import tensorflow as tf
from tensorflow.keras import optimizers, losses, metrics, Model
from abc import ABC, abstractmethod
import yaml
from .graph_sage import GraphSAGE
from ..util import link_classification, sample_features, sample_features_unsupervised
from .sequence import NodeSequence, OnDemandLinkSequence


class NodeClassificationModel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def train(self, data):
        pass

    @abstractmethod
    def load(self, file_path):
        pass

    @abstractmethod
    def save(self, file_path):
        pass

    @abstractmethod
    def predict(self, data):
        pass


class GraphSAGEModel(NodeClassificationModel):
    def __init__(self, config_path, model_path=None):
        super().__init__()
        self.model = None
        if model_path is None:
            with open(config_path) as file:
                self.config = yaml.load(file, Loader=yaml.Loader)
            graph_sage = GraphSAGE(layer_sizes=self.config['GNN']['graphSAGE']['hidden_dims'],
                                   n_samples=self.config['GNN']['graphSAGE']['sample_size'],
                                   input_dim=self.config['GNN']['graphSAGE']['input_dim'],
                                   multiplicity=2)
            self.x_inp, self.x_out = graph_sage.in_out_tensors()
            prediction = link_classification(
                output_dim=1, output_act="sigmoid", edge_embedding_method="ip"
            )(self.x_out)
            self.model = Model(inputs=self.x_inp, outputs=prediction)
            self.model.compile(
                optimizer=optimizers.Adam(lr=1e-3),
                loss=losses.binary_crossentropy,
                metrics=[metrics.binary_accuracy],
            )
        else:
            self.load(model_path)

    def train(self, data):
        train_seq = OnDemandLinkSequence(sample_features_unsupervised,
                                         self.config['GNN']['graphSAGE']['batch_size'],
                                         data.adjacency_matrix,
                                         data.feature,
                                         self.config['GNN']['graphSAGE']['sample_size'])
        self.model.fit(
            train_seq,
            epochs=self.config['GNN']['graphSAGE']['epochs'],
            verbose=2,
            use_multiprocessing=False,
            workers=4,
            shuffle=True,
        )
        x_inp_src = self.x_inp[0::2]
        x_out_src = self.x_out[0]
        self.model = tf.keras.Model(inputs=x_inp_src, outputs=x_out_src)

    def load(self, file_path='models/graph_sage.tf'):
        self.model = tf.keras.models.load_model(file_path)

    def save(self, file_path='models/graph_sage.tf'):
        self.model.save(file_path)

    def predict(self, data):
        node = NodeSequence(sample_features,
                            self.config['GNN']['graphSAGE']['batch_size'],
                            list(data.uid),
                            data.adjacency_matrix,
                            data.feature,
                            self.config['GNN']['graphSAGE']['sample_size'])
        node_embeddings = self.model.predict(node, workers=4, verbose=1)
        return node_embeddings
