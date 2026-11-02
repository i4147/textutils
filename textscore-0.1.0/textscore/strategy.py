import math
from collections.abc import Callable
from enum import Enum


class ComputeStrategy(str, Enum):
    FASTEST = "fastest"
    FAST = "fast"
    OPTIMAL = "optimal"
    ACCURATE = "accurate"

    def stride_factory(self) -> Callable[[int], int]:
        def compute_stride(length: int) -> int:
            if self.value == ComputeStrategy.FASTEST:
                return length
            if self.value == ComputeStrategy.FAST:
                return math.ceil(length / 2)
            if self.value == ComputeStrategy.OPTIMAL:
                return math.ceil(length / 8)
            return 1

        return compute_stride
