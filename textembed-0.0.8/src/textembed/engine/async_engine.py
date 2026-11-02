from typing import List
from textembed.batch import BatchProcessor
from textembed.engine.args import AsyncEngineArgs
from textembed.executor.embedder.sentence_transformer import SentenceTransformerEmbedder
from textembed.log import logger


class AsyncEngine:
    def __init__(self, engine_args: AsyncEngineArgs) -> None:
        self._engine_args = engine_args
        self.running = False
        self.batch_processor = None
        self.model = None

    @classmethod
    def from_args(cls, engine_args: AsyncEngineArgs) -> "AsyncEngine":
        return cls(engine_args)

    async def start(self):
        if self.running:
            logger.warning("The engine is already running.")
            return
        self.model = SentenceTransformerEmbedder(engine_args=self._engine_args)
        self.batch_processor = BatchProcessor(
            model=self.model,
            workers=self._engine_args.workers,
            batch_size=self._engine_args.batch_size,
        )
        self.running = True
        logger.info("Engine started for the %s model.", self._engine_args.model)
        await self.model.warm_up()

    async def stop(self):
        self._check_running()
        self.running = False
        if self.batch_processor is not None:
            await self.batch_processor.shutdown()
        logger.info("Engine stopped for the %s model.", self._engine_args.model)

    def _check_running(self):
        if not self.running:
            raise ValueError("The engine is not running. You must start the engine before using it.")

    @property
    def engine_args(self) -> AsyncEngineArgs:
        return self._engine_args

    async def aembed(self, sentences: List[str], future):
        self._check_running()
        if self.batch_processor is None:
            raise ValueError("Batch processor is not initialized.")
        await self.batch_processor.add_request(sentences, future)
