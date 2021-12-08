__all__ = [
    'NodeClassificationModel',
    'GraphSAGEModel'
]

import os
import tensorflow as tf
from tensorflow.keras import optimizers, losses, metrics, Model
from abc import ABC, abstractmethod
import yaml
from .graph_sage import GraphSAGE
from ..util import link_classification, sample_features_unsupervised
from .sequence import OnDemandLinkSequence


class NodeClassificationModel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def train(self, data):
        pass

    @abstractmethod
    def predict(self, data):
        pass


class GraphSAGEModel(NodeClassificationModel):
    def __init__(self, config_path=None, model_path=None):
        super().__init__()
        self.model = None
        if model_path is None:
            if config_path is None:
                current_path = os.path.dirname(__file__)
                config_path = os.path.join(current_path, 'default_config.yaml')
            with open(config_path) as file:
                self.config = yaml.load(file, Loader=yaml.Loader)
            graph_sage = GraphSAGE(layer_sizes=self.config['GNN']['graphSAGE']['hidden_dims'],
                                   n_samples=self.config['GNN']['graphSAGE']['sample_size'],
                                   input_dim=self.config['GNN']['graphSAGE']['input_dim'],
                                   multiplicity=2)
            x_inp, x_out = graph_sage.in_out_tensors()
            prediction = link_classification(
                output_dim=1, output_act="sigmoid", edge_embedding_method="ip"
            )(x_out)
            self.model = Model(inputs=x_inp, outputs=prediction)

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

    def load(self, filepath=None):
        if filepath is None:
            filepath = 'models/graph_sage.h5'
        self.model = tf.keras.models.load_model(filepath)

    def save(self, filepath=None):
        if filepath is None:
            filepath = 'models/graph_sage.h5'
        self.model.save(filepath)

    def predict(self, data):
        pass
