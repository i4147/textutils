from textwiser.base import BaseFeaturizer
from textwiser.utils import Constants

try:
    import tensorflow as tf
    import tensorflow_hub as hub
except ModuleNotFoundError:
    pass


class _USEEmbeddings(BaseFeaturizer):
    def __init__(self, pretrained="https://tfhub.dev/google/universal-sentence-encoder-large/5"):
        super(_USEEmbeddings, self).__init__()
        self.pretrained = (
            pretrained
            if pretrained is not Constants.default_model
            else "https://tfhub.dev/google/universal-sentence-encoder-large/5"
        )
        self.use = None
        self._ignored_args = {"use"}

    def fit(self, x, y=None):
        self.use = hub.KerasLayer(self.pretrained)

    def forward(self, x):
        try:
            return self.use(tf.constant(x)).numpy()
        except AttributeError:
            return self.use(x)["outputs"].numpy()
