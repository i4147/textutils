import copy
from enum import Enum
import os
from typing import Callable, Dict, List, NamedTuple, Optional, Union
from textwiser.utils import check_true, check_false, Constants, set_params


class WordOptions(Enum):
    bytepair = "bytepair"
    char = "char"
    word2vec = "word2vec"
    flair = "flair"
    elmo = "elmo"
    bert = "bert"
    gpt = "gpt"
    gpt2 = "gpt2"
    transformerXL = "transformerXL"
    xlnet = "xlnet"
    xlm = "xlm"
    roberta = "roberta"
    distilbert = "distilbert"
    ctrl = "ctrl"
    albert = "albert"
    t5 = "t5"
    xlm_roberta = "xlm_roberta"
    bart = "bart"
    electra = "electra"
    dialo_gpt = "dialo_gpt"
    longformer = "longformer"

    def is_finetuneable(self):
        return self not in (WordOptions.elmo,)

    def is_from_transformers(self):
        return self in (
            WordOptions.bert,
            WordOptions.gpt,
            WordOptions.gpt2,
            WordOptions.transformerXL,
            WordOptions.xlnet,
            WordOptions.xlm,
            WordOptions.roberta,
            WordOptions.distilbert,
            WordOptions.ctrl,
            WordOptions.albert,
            WordOptions.t5,
            WordOptions.xlm_roberta,
            WordOptions.bart,
            WordOptions.electra,
            WordOptions.dialo_gpt,
            WordOptions.longformer,
        )


class PoolOptions(Enum):
    max = "max"
    min = "min"
    mean = "mean"
    first = "first"
    last = "last"


class _ArgBase:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._frozen = True

    def _set(self, key, value):
        self.__setattr__(key, value, force=True)

    def __setattr__(self, key, value, force=False):
        if force or not hasattr(self, Constants.frozen) or not self._frozen:
            super().__setattr__(key, value)
        else:
            raise ValueError("Embeddings and Transformations are immutable!")

    def _get_attrs(self):
        return {k: v for k, v in self.__dict__.items() if k not in (Constants.kwargs, Constants.frozen)}

    def set_params(self, **kwargs):
        set_params(self, **kwargs)

    def _validate(self, finetune_enabled=False):
        pass

    def _is_finetuneable(self):
        return isinstance(
            self,
            (
                Embedding.Word,
                Transformation.SVD,
            ),
        )

    def _can_backprop(self):
        return isinstance(
            self,
            (
                Transformation.Pool,
                Transformation.SVD,
            ),
        )

    @staticmethod
    def from_string(model_name: str, params=None):
        classes = [c for c in _ArgBase.__subclasses__() if c != _EmbeddingBase] + [
            c for c in _EmbeddingBase.__subclasses__()
        ]
        converter = {c.__name__.lower(): c for c in classes}
        if not params:
            params = dict()
        if model_name in converter:
            return converter.get(model_name)(**params)
        else:
            raise ValueError("The string embedding or transformation type %s is not supported." % model_name)


class _EmbeddingBase(_ArgBase):
    def __init__(self, pretrained=Constants.default_model, **kwargs):
        self.pretrained = pretrained
        super().__init__(**kwargs)


class Embedding(NamedTuple):
    class BOW(_EmbeddingBase):
        def _validate(self, finetune_enabled=False):
            check_true(
                not self.pretrained
                or self.pretrained is Constants.default_model
                or (isinstance(self.pretrained, str) and os.path.exists(self.pretrained))
                or hasattr(self.pretrained, "read"),
                ValueError("The pretrained model should be a path to a pickle file or a file-like object."),
            )

    class Compound(_EmbeddingBase):
        def __init__(self, schema: Union[Dict, list, tuple, str] = None, pretrained=Constants.default_model, **kwargs):
            self.schema = copy.deepcopy(schema)
            super().__init__(pretrained=pretrained, **kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(
                isinstance(self.schema, (dict, str, tuple, list)),
                TypeError(
                    "The schema should either be a dictionary, a valid embedding, an embedding-parameters tuple, or the path to a JSON file."
                ),
            )
            check_true(
                self.pretrained is None or self.pretrained is Constants.default_model,
                ValueError("Compound embeddings cannot be pretrained. Save the TextWiser object instead."),
            )

        def _is_finetuneable(self, schema=None):
            def can_backprop(transformation):
                if isinstance(transformation, (str, tuple, list)):
                    kwargs = dict()
                    if isinstance(transformation, (tuple, list)):
                        kwargs = transformation[1]
                        transformation = transformation[0]
                    return _ArgBase.from_string(transformation, kwargs)._can_backprop()

            schema = schema if schema else self.schema
            if isinstance(schema, (str, tuple, list)):
                kwargs = dict()
                if isinstance(schema, (tuple, list)):
                    kwargs = schema[1]
                    schema = schema[0]
                if schema in WordOptions.__members__:
                    return Embedding.Word(word_option=WordOptions[schema], **kwargs)._is_finetuneable()
                return _ArgBase.from_string(schema, kwargs)._is_finetuneable()
            if "transform" in schema:
                transforms = schema["transform"]
                for transformation in transforms[:0:-1]:
                    if self._is_finetuneable(schema=transformation):
                        return True
                    elif not can_backprop(transformation):
                        return False
                return self._is_finetuneable(schema=transforms[0])
            if "concat" in schema:
                concats = schema["concat"]
                return any([self._is_finetuneable(concat) for concat in concats])

    class Doc2Vec(_EmbeddingBase):
        def __init__(
            self,
            deterministic: bool = False,
            tokenizer: Optional[Callable[[str], List[str]]] = None,
            pretrained=Constants.default_model,
            **kwargs,
        ):
            self.deterministic = deterministic
            self.tokenizer = tokenizer
            super().__init__(pretrained=pretrained, **kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(
                isinstance(self.deterministic, bool), TypeError("The deterministic parameter should be a boolean.")
            )
            if self.tokenizer:
                doc = "string"
                res = self.tokenizer(doc)
                check_true(isinstance(res, list), TypeError("The tokenizer should return a list of tokens."))
                check_true(isinstance(res[0], str), TypeError("The tokens should be of string type."))
            check_true(
                not self.pretrained
                or self.pretrained is Constants.default_model
                or (isinstance(self.pretrained, str) and os.path.exists(self.pretrained))
                or hasattr(self.pretrained, "read"),
                ValueError("The pretrained model should be a path to a pickle file or a file-like object."),
            )

    class Random(_EmbeddingBase):
        def _validate(self, finetune_enabled=False):
            check_true(
                self.pretrained is None or self.pretrained is Constants.default_model,
                ValueError("Random embeddings cannot be pretrained. Save the TextWiser object instead."),
            )

    class TfIdf(_EmbeddingBase):
        def _validate(self, finetune_enabled=False):
            check_true(
                not self.pretrained
                or self.pretrained is Constants.default_model
                or (isinstance(self.pretrained, str) and os.path.exists(self.pretrained))
                or hasattr(self.pretrained, "read"),
                ValueError("The pretrained model should be a path to a pickle file or a file-like object."),
            )

    class USE(_EmbeddingBase):
        def _validate(self, finetune_enabled=False):
            import tensorflow
            import tensorflow_hub

            check_true(self.pretrained, ValueError("USE needs to be pretrained."))

    class Word(_EmbeddingBase):
        def __init__(
            self,
            word_option: WordOptions = WordOptions.word2vec,
            pretrained: str = Constants.default_model,
            sparse: bool = False,
            tokenizer: Optional[Callable[[str], List[str]]] = None,
            layers: Union[int, List[int]] = -1,
            inline_pool_option: Optional[PoolOptions] = None,
            **kwargs,
        ):
            self.word_option = word_option
            self.sparse = sparse
            self.tokenizer = tokenizer
            self.layers = layers
            self.inline_pool_option = inline_pool_option
            super().__init__(pretrained=pretrained, **kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(
                isinstance(self.word_option, WordOptions),
                ValueError("The embedding must be one of the supported word embeddings."),
            )
            check_true(
                self.pretrained or self.word_option is WordOptions.word2vec,
                ValueError("Only word2vec embeddings can be trained from scratch."),
            )
            check_true(
                not finetune_enabled or self._is_finetuneable(),
                ValueError("The weights can only be fine-tuned if they are not ELMo embeddings."),
            )
            check_false(
                not finetune_enabled and self.word_option == WordOptions.char,
                ValueError("Character embeddings are only available if the model is fine-tuneable."),
            )
            check_true(
                not self.sparse or self.word_option == WordOptions.word2vec,
                ValueError("Sparse embeddings only supported with word2vec embeddings"),
            )
            check_true(
                isinstance(self.layers, int) or all([isinstance(l, int) for l in self.layers]),
                ValueError("Layers can only be an integer or a list of integers"),
            )
            check_true(
                not self.inline_pool_option or isinstance(self.inline_pool_option, PoolOptions),
                ValueError("Inline pooling should either be None or a pool option."),
            )
            if self.word_option == WordOptions.elmo:
                import tensorflow
                import tensorflow_hub

                check_true(self.pretrained, ValueError("ELMo needs to be pretrained."))
            if self.tokenizer:
                check_true(
                    self.word_option == WordOptions.word2vec,
                    ValueError("The tokenizer can only be used if word2vec embeddings are used."),
                )
                doc = "string"
                res = self.tokenizer(doc)
                check_true(isinstance(res, list), TypeError("The tokenizer should return a list of tokens."))
                check_true(isinstance(res[0], str), TypeError("The tokens should be of string type."))

        def _is_finetuneable(self):
            return self.word_option.is_finetuneable()


class Transformation(NamedTuple):
    class LDA(_ArgBase):
        def __init__(self, n_components: int = 10, **kwargs):
            self.n_components = n_components
            super().__init__(**kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(isinstance(self.n_components, int), TypeError("The number of components must be an integer."))
            check_true(self.n_components >= 2, ValueError("The number of components must be at least two."))

    class NMF(_ArgBase):
        def __init__(self, n_components: int = 10, **kwargs):
            self.n_components = n_components
            super().__init__(**kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(isinstance(self.n_components, int), TypeError("The number of components must be an integer."))
            check_true(self.n_components >= 2, ValueError("The number of components must be at least two."))

    class UMAP(_ArgBase):
        def __init__(
            self,
            n_components: int = 10,
            random_state: Optional[int] = Constants.default_seed,
            deterministic_init: bool = True,
            **kwargs,
        ):
            self.n_components = n_components
            self.random_state = random_state
            self.deterministic_init = deterministic_init
            super().__init__(**kwargs)

        def _validate(self, finetune_enabled=False):
            import umap

            check_true(isinstance(self.n_components, int), TypeError("The number of components must be an integer."))
            check_true(self.n_components >= 2, ValueError("The number of components must be at least two."))
            check_true(isinstance(self.n_components, int), TypeError("The number of components must be an integer."))
            check_true(
                self.random_state is None or isinstance(self.random_state, int),
                TypeError("The random seed must be an integer or ``None``."),
            )
            check_true(
                isinstance(self.deterministic_init, bool),
                TypeError("The deterministic init parameter must be a boolean."),
            )
            check_true(
                not self.deterministic_init or self.random_state is not None,
                ValueError("If deterministic init parameter is ``True``, the random state must also be specified."),
            )
            check_true(
                not self.deterministic_init or "init" not in self.kwargs,
                ValueError("If deterministic init parameter is ``True``, you cannot pass an ``init``parameter to UMAP"),
            )

    class Pool(_ArgBase):
        def __init__(self, pool_option: PoolOptions = PoolOptions.max, **kwargs):
            self.pool_option = pool_option
            super().__init__(**kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(
                isinstance(self.pool_option, PoolOptions), TypeError("The pool type must be models.options.PoolOptions")
            )

    class SVD(_ArgBase):
        def __init__(self, n_components: int = 10, **kwargs):
            self.n_components = n_components
            super().__init__(**kwargs)

        def _validate(self, finetune_enabled=False):
            check_true(isinstance(self.n_components, int), TypeError("The number of components must be an integer."))
            check_true(self.n_components >= 2, ValueError("The number of components must be at least two."))


Embedding_Type = Union[
    Embedding.BOW,
    Embedding.Compound,
    Embedding.Doc2Vec,
    Embedding.Random,
    Embedding.TfIdf,
    Embedding.USE,
    Embedding.Word,
]
Transformation_Type = Union[
    Transformation.LDA, Transformation.NMF, Transformation.Pool, Transformation.SVD, Transformation.UMAP
]
