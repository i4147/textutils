import asyncio
import time
from asyncio import Queue
from typing import List
from textembed.executor.embedder.sentence_transformer import SentenceTransformerEmbedder
from textembed.log import logger


class BatchProcessor:
    def __init__(
        self,
        model: SentenceTransformerEmbedder,
        workers: int,
        batch_size: int,
    ) -> None:
        self.model = model
        self.workers = workers
        self.batch_size = batch_size
        self.request_queue: Queue = Queue()
        self.loop = asyncio.get_running_loop()
        self.worker_tasks = [self.loop.create_task(self.batch_processor(i)) for i in range(workers)]
        self.loop.create_task(self._log_workers_started())

    async def _log_workers_started(self):
        await asyncio.sleep(0)
        logger.info(
            "All %d workers have started batch processing for the %s model.",
            self.workers,
            self.model.engine_args.model,
        )

    async def batch_processor(self, worker_id: int):
        logger.debug(
            "Worker with ID %d has started batch processing for the %s model.",
            worker_id,
            self.model.engine_args.model,
        )
        while True:
            start_time = time.perf_counter()
            requests = []
            try:
                while len(requests) < self.batch_size:
                    request = await asyncio.wait_for(self.request_queue.get(), timeout=0.05)
                    requests.append(request)
            except asyncio.TimeoutError:
                pass
            if requests:
                all_texts = [text for req in requests for text in req[0]]
                futures = [req[1] for req in requests]
                try:
                    embeddings, usage = await self.model.process_batch(all_texts)
                    idx = 0
                    for future, req in zip(futures, requests):
                        num_texts = len(req[0])
                        future.set_result((
                            embeddings[idx : idx + num_texts],
                            usage[idx : idx + num_texts],
                        ))
                        idx += num_texts
                except Exception as e:
                    for future in futures:
                        future.set_exception(e)
                logger.debug(
                    "Worker %d processed batch in %.4f ms",
                    worker_id,
                    (time.perf_counter() - start_time) * 1000,
                )

    async def add_request(self, texts: List[str], future: asyncio.Future):
        await self.request_queue.put((texts, future))

    async def shutdown(self):
        for task in self.worker_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Worker task cancelled.")
