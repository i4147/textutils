from typing import Iterable, Iterator, List, Union
from .args import AsyncEngineArgs
from .async_engine import AsyncEngine


class AsyncEngineArray:
    def __init__(self, engines: Iterable["AsyncEngine"]):
        if not engines:
            raise ValueError("Engines collection cannot be empty.")
        unique_model_names = set(engine.engine_args.served_model_name for engine in engines)
        if len(list(engines)) != len(unique_model_names):
            raise ValueError("Each engine must have a unique served model name.")
        self.engines_dict = {engine.engine_args.served_model_name: engine for engine in engines}

    @classmethod
    def from_args(cls, engine_args_list: Iterable[AsyncEngineArgs]) -> "AsyncEngineArray":
        engines = map(AsyncEngine.from_args, engine_args_list)
        return cls(engines=tuple(engines))

    @property
    def engine_args(self) -> List[AsyncEngineArgs]:
        return [engine.engine_args for engine in self.engines_dict.values()]

    def __iter__(self) -> Iterator["AsyncEngine"]:
        return iter(self.engines_dict.values())

    async def start_all(self):
        for engine in self.engines_dict.values():
            await engine.start()

    async def stop_all(self):
        for engine in self.engines_dict.values():
            await engine.stop()

    def __getitem__(self, key: Union[str, int]) -> "AsyncEngine":
        if len(self.engines_dict) == 1:
            return list(self.engines_dict.values())[0]
        if isinstance(key, int):
            return list(self.engines_dict.values())[key]
        if isinstance(key, str) and key in self.engines_dict:
            return self.engines_dict[key]
        raise IndexError(
            f"Engine for model name `{key}` not found. Available model names are {list(self.engines_dict.keys())}."
        )
