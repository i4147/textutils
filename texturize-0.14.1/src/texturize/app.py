import itertools
import dataclasses
import torch
import torch.nn.functional as F
from .logger import get_default_log
from .solvers import (
    SolverSGD,
    SolverLBFGS,
    MultiCriticObjective,
    SequentialCriticObjective,
)
from .io import *

__all__ = ["Application", "Result", "TextureSynthesizer"]


class TextureSynthesizer:
    def __init__(self, device, encoder, lr, iterations):
        self.device = device
        self.encoder = encoder
        self.iterations = iterations
        self.learning_rate = lr

    def run(self, progress, seed_img, *args):
        for oc, sc in itertools.product(
            [MultiCriticObjective, SequentialCriticObjective],
            [SolverLBFGS, SolverSGD],
        ):
            if sc == SolverLBFGS and seed_img.dtype == torch.float16:
                continue
            try:
                yield from self._run(progress, seed_img, *args, objective_class=oc, solver_class=sc)
                progress.finish()
                return
            except RuntimeError as e:
                if "CUDA out of memory." not in str(e):
                    raise
                import gc

                gc.collect
                torch.cuda.empty_cache()
        raise RuntimeError("CUDA out of memory.")

    def _run(self, progress, seed_img, critics, objective_class=None, solver_class=None):
        critics = list(itertools.chain.from_iterable(critics))
        image = seed_img.to(self.device)
        alpha = None if image.shape[1] == 3 else image[:, 3:4]
        image = image[:, 0:3].detach().requires_grad_(True)
        obj = objective_class(self.encoder, critics, alpha=alpha)
        opt = solver_class(obj, image, lr=self.learning_rate)
        for i, loss, lr, retries in self._iterate(opt):
            image.data.clamp_(0.0, 1.0)
            progress.update(i * 100 / (self.iterations - 1), loss=loss, iter=i)
            yield loss, image, lr, retries
        progress.max_value = i + 1

    def _iterate(self, opt):
        for i in range(self.iterations):
            loss, scores = opt.step()
            yield i, loss, opt.lr, opt.retries


@dataclasses.dataclass
class Result:
    tensor: torch.Tensor
    octave: int
    scale: int
    iteration: int
    loss: float
    rate: float
    retries: int

    @property
    def images(self):
        return save_tensor_to_images(self.tensor)


class Application:
    def __init__(self, log=None, device=None, precision=None):
        self.log = log or get_default_log()
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.precision = getattr(torch, precision or "float32")

    def process_octave(self, result_img, encoder, critics, octave, scale, iterations):
        synth = TextureSynthesizer(self.device, encoder, lr=0.1, iterations=iterations)
        result_img = result_img.to(dtype=self.precision)
        yield Result(result_img, octave, scale, 0, float("+inf"), 1.0, 0)
        for iteration, (loss, result_img, lr, retries) in enumerate(
            synth.run(self.progress, result_img, critics), start=1
        ):
            yield Result(result_img, octave, scale, iteration, loss, lr, retries)
        yield Result(result_img, octave, scale, -iteration, loss, lr, retries)
