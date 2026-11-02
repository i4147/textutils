from typing import List, Union
import warnings
import numpy as np
import torch
from textwiser.base import BaseFeaturizer
from textwiser.factory import get_standalone_document_embeddings, _Sequential
from textwiser.options import _ArgBase, Embedding, Embedding_Type, Transformation, Transformation_Type
from textwiser.utils import check_true, check_false, convert, device, OutputType


class TextWiser(BaseFeaturizer):
    def __init__(
        self,
        embedding: Embedding_Type,
        transformations: Union[None, Transformation_Type, List[Transformation_Type]] = None,
        is_finetuneable: bool = False,
        dtype: Union[np.generic, torch.dtype] = np.float32,
        lazy_load: bool = False,
    ):
        super(TextWiser, self).__init__()
        if transformations:
            if isinstance(transformations, _ArgBase):
                transformations = [transformations]
        TextWiser._validate_init_args(embedding, transformations, is_finetuneable, dtype)
        self.embedding = embedding
        self.transformations = transformations
        self.is_finetuneable = is_finetuneable
        self.dtype = dtype
        self.is_fitted = False
        self._imp = None
        if not lazy_load:
            self._init_all_models()

    def _init_all_models(self):
        models = [self._init_model(self.embedding)]
        if self.transformations:
            models.extend([self._init_model(transformation) for transformation in self.transformations])
        self._imp = _Sequential(*models)
        self.to(device)

    def _init_model(self, model: Union[Embedding_Type, Transformation_Type]):
        return get_standalone_document_embeddings(model)

    def fit(self, x=None, y=None):
        self._validate_fit_args(x, y)
        if not self._imp:
            self._init_all_models()
        self.train()
        self._imp.fit(self._standardize_input(x), y)
        self.is_fitted = True
        return self

    def _standardize_input(self, x):
        if isinstance(x, str):
            return [x]
        elif x is None:
            return []
        return x

    def _convert_to_dtype(self, x, detach=False):
        typ = OutputType.tensor if isinstance(self.dtype, torch.dtype) else OutputType.array
        return convert(x, typ, self.dtype, detach=detach)

    def forward(self, x):
        if self.is_fitted:
            x = self._standardize_input(x)
            if self.is_finetuneable:
                return self._forward(x)
            else:
                self.eval()
                with torch.no_grad():
                    return self._forward(x, detach=True)
        else:
            raise NotImplementedError("You must call the `fit` method before featurizing the text.")

    def _forward(self, x, detach=False):
        return self._convert_to_dtype(self._imp(x), detach=detach)

    def fit_transform(self, x, y=None):
        self._validate_fit_args(x, y)
        if not self._imp:
            self._init_all_models()
        if self.is_finetuneable:
            self.train()
            x = self._convert_to_dtype(self._imp.fit_transform(self._standardize_input(x), y))
        else:
            self.eval()
            with torch.no_grad():
                x = self._convert_to_dtype(self._imp.fit_transform(self._standardize_input(x), y), detach=True)
        self.is_fitted = True
        return x

    @staticmethod
    def _check_finetuneable(embedding, transformations):
        if transformations:
            for transformation in transformations[::-1]:
                if transformation._is_finetuneable():
                    return True
                elif not transformation._can_backprop():
                    return False
        return embedding._is_finetuneable()

    @staticmethod
    def _validate_init_args(embedding, transformations, is_finetuneable, dtype):
        embedding._validate(finetune_enabled=is_finetuneable)
        if transformations:
            [transformation._validate() for transformation in transformations]
        if (
            isinstance(embedding, Embedding.Word)
            and embedding.inline_pool_option is None
            and (
                not transformations
                or not any([isinstance(transformation, Transformation.Pool) for transformation in transformations])
            )
        ):
            warnings.warn(
                "Word embeddings are specified but no pool options are specified. Are you sure you don't want to pool them?",
                RuntimeWarning,
            )
        check_false(
            isinstance(embedding, Embedding.Word)
            and embedding.inline_pool_option is not None
            and transformations
            and any([isinstance(transformation, Transformation.Pool) for transformation in transformations]),
            ValueError(
                "You cannot specify both `inline_pool_option` and `Pool` transformation for the same"
                " embedding at the same time. Please pick one!"
            ),
        )
        check_true(
            isinstance(dtype, torch.dtype) or issubclass(dtype, np.generic),
            TypeError("The dtype must be either a numpy or torch type."),
        )
        check_true(
            not is_finetuneable or isinstance(dtype, torch.dtype),
            TypeError("The dtype must be torch for model to be fine-tuneable."),
        )
        check_true(
            not is_finetuneable or TextWiser._check_finetuneable(embedding, transformations),
            ValueError("Model must have fine-tuneable weights if `is_finetuneable` is specified."),
        )

    @staticmethod
    def _validate_fit_args(x, y):
        pass
