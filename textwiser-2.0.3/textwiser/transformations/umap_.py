import numpy as np
from textwiser.transformations.nmf import _ScikitTransformation
from textwiser.utils import OutputType, convert

try:
    from umap import UMAP

    model = UMAP
except ModuleNotFoundError:
    model = None


class _UMAPTransformation(_ScikitTransformation):
    Model = model

    def __init__(self, model=None, deterministic_init: bool = False, **kwargs):
        super().__init__(model=model, **kwargs)
        self.deterministic_init = deterministic_init

    def _get_deterministic_init(self, x: np.ndarray):
        return np.random.default_rng(self.init_args["random_state"]).uniform(
            low=-10.0, high=10.0, size=(x.shape[0], self.init_args["n_components"])
        )

    def _fit(self, x, y=None):
        if self.deterministic_init:
            self.model = self.Model(**self.init_args, init=self._get_deterministic_init(x))
        else:
            self.model = self.Model(**self.init_args)
        self.model.fit(x, convert(y, OutputType.array))

    def _fit_transform(self, x, y=None):
        if self.deterministic_init:
            self.model = self.Model(**self.init_args, init=self._get_deterministic_init(x))
        else:
            self.model = self.Model(**self.init_args)
        return self.model.fit_transform(x, convert(y, OutputType.array)).astype(np.float32)

    @property
    def input_types(self):
        return (OutputType.array,)
