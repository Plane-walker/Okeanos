__all__ = [
    'NodeClassificationModel',
    'GraphSAGEModel'
]

import tensorflow as tf
from tensorflow.keras import optimizers, losses, metrics, Model
from abc import ABC, abstractmethod
import yaml
import os
from log import log
import numpy as np
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
    def load(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def predict(self, data):
        pass


class GraphSAGEModel(NodeClassificationModel):
    def __init__(self, config_path, model_path=None):
        super().__init__()
        self.config_path = config_path
        self.model = None
        if model_path is None:
            with open(config_path) as file:
                config = yaml.load(file, Loader=yaml.Loader)
            graph_sage = GraphSAGE(layer_sizes=config['GNN']['graphSAGE']['hidden_dims'],
                                   n_samples=config['GNN']['graphSAGE']['sample_size'],
                                   input_dim=config['GNN']['graphSAGE']['input_dim'],
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
            self.load()

    def train(self, data):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        id_map, features, adjacency_matrix, labels = data.get_all_data()
        train_seq = OnDemandLinkSequence(sample_features_unsupervised,
                                         config['GNN']['graphSAGE']['batch_size'],
                                         adjacency_matrix,
                                         features,
                                         config['GNN']['graphSAGE']['sample_size'])
        self.model.fit(
            train_seq,
            epochs=config['GNN']['graphSAGE']['epochs'],
            verbose=2,
            use_multiprocessing=False,
            workers=4,
            shuffle=True,
        )
        x_inp_src = self.x_inp[0::2]
        x_out_src = self.x_out[0]
        self.model = tf.keras.Model(inputs=x_inp_src, outputs=x_out_src)

    def load(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.model = tf.keras.models.load_model(os.path.join(config['GNN']['base_path'], config['GNN']['model_path']))

    def save(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.model.save(os.path.join(config['GNN']['base_path'], config['GNN']['model_path']))

    def predict(self, data):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        id_map, features, adjacency_matrix, labels = data.get_all_data()
        node = NodeSequence(sample_features,
                            config['GNN']['graphSAGE']['batch_size'],
                            list(range(len(features))),
                            adjacency_matrix,
                            features,
                            config['GNN']['graphSAGE']['sample_size'])
        node_embeddings = self.model.predict(node, workers=4, verbose=1)
        log.info(f'GraphSAGE predict node_embeddings is {node_embeddings}')
        self_index = np.where(id_map == config['app']['app_id'])
        node_embedding = node_embeddings[self_index]
        group = np.where(node_embeddings == node_embedding)
        for vertex_index in group:
            if vertex_index != self_index:
                return labels[vertex_index]
        return labels[self_index]
