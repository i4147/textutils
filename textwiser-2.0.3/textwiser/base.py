import abc
import torch.nn as nn
from textwiser.utils import set_params


class BaseFeaturizer(abc.ABC, nn.Module):
    @abc.abstractmethod
    def fit(self, x, y=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def forward(self, x):
        raise NotImplementedError()

    def transform(self, x):
        return self(x)

    def fit_transform(self, x, y=None):
        self.fit(x, y)
        return self.transform(x)

    def set_params(self, **kwargs):
        set_params(self, **kwargs)

    def state_dict(self, destination=None, prefix="", keep_vars=False):
        sd = super(BaseFeaturizer, self).state_dict(destination, prefix, keep_vars)
        ignored_args = {
            "_backend",
            "_parameters",
            "_buffers",
            "_backward_hooks",
            "_forward_hooks",
            "_forward_pre_hooks",
            "_state_dict_hooks",
            "_load_state_dict_pre_hooks",
            "_modules",
            "training",
        }
        try:
            ignored_args |= self._ignored_args
        except AttributeError:
            pass
        saved_args = [k for k in self.__dict__.keys() if k not in ignored_args]
        for varname in saved_args:
            sd[prefix + varname] = getattr(self, varname)
        sd[prefix + "_saved_args"] = saved_args
        return sd

    def _load_from_state_dict(
        self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs
    ):
        saved_args = prefix + "_saved_args"
        if saved_args in state_dict:
            for varname in state_dict[saved_args]:
                setattr(self, varname, state_dict[prefix + varname])
                state_dict.pop(prefix + varname)
            state_dict.pop(saved_args)
        super(BaseFeaturizer, self)._load_from_state_dict(
            state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs
        )
