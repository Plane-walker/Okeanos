from tensorflow.keras import optimizers, losses, metrics, Model
import yaml
from dock.gnn.graphSAGE import GraphSAGE
from dock.util.util import link_classification, sample_features_unsupervised
from sequence import OnDemandLinkSequence


class NodeClassification:
    def __init__(self, data, method):
        self.data = data
        self.method = method
        if method == 'graphSAGE':
            with open('default_config.yaml') as file:
                self.default_config = yaml.load(file, Loader=yaml.Loader)
            graph_sage = GraphSAGE(layer_sizes=self.default_config['GNN']['graphSAGE']['hidden_dims'],
                                   n_samples=self.default_config['GNN']['graphSAGE']['sample_size'],
                                   input_dim=data.feature.shape[1],
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

    def train(self):
        train_seq = OnDemandLinkSequence(sample_features_unsupervised,
                                         self.default_config['GNN']['graphSAGE']['batch_size'],
                                         self.data.adjacency_matrix,
                                         self.data.feature,
                                         self.default_config['GNN']['graphSAGE']['sample_size'])
        history = self.model.fit(
            train_seq,
            epochs=self.default_config['GNN']['graphSAGE']['epochs'],
            verbose=2,
            use_multiprocessing=False,
            workers=4,
            shuffle=True,
        )

    def predict(self):
        pass
