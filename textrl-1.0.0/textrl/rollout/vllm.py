from typing import Any


def vllm_config(
    tensor_parallel_size: int = 1,
    gpu_memory_utilization: float = 0.6,
    dtype: str = "auto",
    max_model_len: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    try:
        import vllm
    except ImportError as e:
        raise ImportError("vLLM rollout requires vllm. Install with: pip install 'textrl[vllm]'") from e
    cfg: dict[str, Any] = {
        "use_vllm": True,
        "vllm_gpu_memory_utilization": gpu_memory_utilization,
        "vllm_dtype": dtype,
    }
    if tensor_parallel_size != 1:
        cfg["vllm_tensor_parallel_size"] = tensor_parallel_size
    if max_model_len is not None:
        cfg["vllm_max_model_len"] = max_model_len
    cfg.update(extra)
    return cfg
