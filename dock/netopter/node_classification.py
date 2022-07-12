__all__ = [
    'NodeClassificationModel',
    'GraphSAGEModel'
]

import tensorflow as tf
from tensorflow.keras import optimizers, losses, Model, layers
from abc import ABC, abstractmethod
import yaml
import os
from log import log
import numpy as np
from dock.netopter.graph_sage import GraphSAGE
from dock.util import sample_features
from dock.netopter.sequence import NodeSequence


class NodeClassificationModel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def init_model(self):
        pass

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def save_model(self):
        pass

    @abstractmethod
    def train(self, data):
        pass

    @abstractmethod
    def predict(self, data):
        pass


class GraphSAGEModel(NodeClassificationModel):
    def __init__(self, config_path, chain_manager):
        super().__init__()
        self.config_path = config_path
        self.chain_manager = chain_manager
        self.model = None
        self.x_input = None
        self.x_output = None
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        if not os.path.exists(os.path.join(config['GNN']['base_path'], config['GNN']['model_path'])):
            self.model, self.x_input, self.x_output = self.init_model()
        else:
            self.model = self.load_model()

    def init_model(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        graph_sage = GraphSAGE(layer_sizes=config['GNN']['graphSAGE']['hidden_dims'],
                               n_samples=config['GNN']['graphSAGE']['sample_size'],
                               input_dim=config['GNN']['graphSAGE']['input_dim'],
                               multiplicity=1)
        x_input, x_output = graph_sage.in_out_tensors()
        prediction = layers.Dense(units=config['GNN']['graphSAGE']['output_dim'], activation="softmax")(x_output)
        model = Model(inputs=x_input, outputs=prediction)
        model.compile(
            optimizer=optimizers.Adam(lr=0.005),
            loss=losses.categorical_crossentropy,
            metrics=["acc"],
        )
        return model, x_input, x_output

    def load_model(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        return tf.keras.models.load_model(os.path.join(config['GNN']['base_path'], config['GNN']['model_path']))

    def save_model(self):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        self.model.save(os.path.join(config['GNN']['base_path'], config['GNN']['model_path']))

    def train(self, data):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        id_map, features, adjacency_matrix, labels = data.import_data()
        train_cut = features.shape[0] // 10 * 8
        train_seq = NodeSequence(sample_features,
                                 config['GNN']['graphSAGE']['batch_size'],
                                 list(range(0, train_cut)),
                                 adjacency_matrix,
                                 features,
                                 config['GNN']['graphSAGE']['sample_size'],
                                 targets=labels[list(range(0, train_cut))])
        test_seq = NodeSequence(sample_features,
                                config['GNN']['graphSAGE']['batch_size'],
                                list(range(train_cut, features.shape[0])),
                                adjacency_matrix,
                                features,
                                config['GNN']['graphSAGE']['sample_size'],
                                targets=labels[list(range(train_cut, features.shape[0]))])
        self.model.fit(
            train_seq, epochs=20, validation_data=test_seq, verbose=2, shuffle=False
        )

    @staticmethod
    def edge_cut(adjacency_matrix, labels):
        edge_cuts = 0
        edges = 0
        for vertex_pair in np.where(adjacency_matrix > 0):
            if labels[vertex_pair[0]] != labels[vertex_pair[1]]:
                edge_cuts += 1
            edges += 1
        return edge_cuts / edges

    @staticmethod
    def balance(labels):
        _, counts = np.unique(labels, return_counts=True)
        return np.max(counts) * np.shape(np.unique(labels))[0] / np.shape(labels)[0]

    @staticmethod
    def modularity(status, resolution):
        links = float(status.total_weight)
        result = 0.
        for community in set(status.communities.values()):
            in_degree = community.internal_degrees
            degree = community.total_degrees
            if links > 0:
                result += in_degree * resolution / links - ((degree / (2. * links)) ** 2)
        return result

    def predict(self, data):
        with open(self.config_path) as file:
            config = yaml.load(file, Loader=yaml.Loader)
        with open(os.path.join(config['chain_manager']['base_path'],
                               self.chain_manager.get_island()[0].chain_name,
                               'config/priv_validator_key.json')) as file:
            priv_validator_key = yaml.load(file, Loader=yaml.Loader)
        self_node_id = priv_validator_key['address']
        id_map, features, adjacency_matrix, labels = data.import_data()
        node = NodeSequence(sample_features,
                            config['GNN']['graphSAGE']['batch_size'],
                            list(range(len(features))),
                            adjacency_matrix,
                            features,
                            config['GNN']['graphSAGE']['sample_size'])
        node_embeddings = self.model.predict(node, workers=4, verbose=1)
        self_index = np.argwhere(id_map == self_node_id)[0][0]
        log.info(f'Node embedding is {node_embeddings[self_index]}')
        node_classes = np.argmax(node_embeddings, axis=1)
        node_class = node_classes[self_index]
        group = np.where(node_class == node_classes)
        for vertex_index in np.nditer(group):
            if vertex_index != self_index:
                return labels[vertex_index]
        return labels[self_index]
