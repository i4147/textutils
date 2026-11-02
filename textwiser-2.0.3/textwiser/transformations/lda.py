from sklearn.decomposition import LatentDirichletAllocation
from textwiser.transformations.nmf import _ScikitTransformation


class _LDATransformation(_ScikitTransformation):
    Model = LatentDirichletAllocation
