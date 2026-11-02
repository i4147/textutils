import asyncio
import base64
import time
from io import BytesIO
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import ORJSONResponse
from PIL import Image
from textembed.api.dependencies import valid_token_dependency
from textembed.api.errors import ModelNotFoundException
from textembed.api.schemas import (
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelDetails,
    ModelList,
    Usage,
)
from textembed.engine.args import AsyncEngineArgs
from textembed.engine.async_engine import AsyncEngine
from textembed.engine.async_engine_array import AsyncEngineArray
from textembed.log import logger

embed_router = APIRouter(prefix="/v1", tags=["Embedding"])


@embed_router.get(
    "/models",
    response_class=ORJSONResponse,
    response_model=ModelList,
    status_code=status.HTTP_200_OK,
)
async def get_models(request: Request) -> ModelList:
    async_engine_args_list: List[AsyncEngineArgs] = request.app.state.async_engine_array.engine_args
    return ModelList(
        data=[
            ModelDetails(
                id=engine_args.model,
                served_model_name=engine_args.served_model_name,
            )
            for engine_args in async_engine_args_list
        ]
    )


async def get_engine(request: Request, embed_request: EmbeddingRequest):
    async_engine_array: AsyncEngineArray = request.app.state.async_engine_array
    async_engine_args_list: List[AsyncEngineArgs] = async_engine_array.engine_args
    if embed_request.model not in [engine_args.model for engine_args in async_engine_args_list]:
        raise ModelNotFoundException(
            message=f"The requested model `{embed_request.model}` was not found. "
            f"Please ensure that you have specified the correct model name. "
            f"Currently served models `{[engine_args.model for engine_args in async_engine_args_list]}`."
        )
    engine: AsyncEngine = async_engine_array[embed_request.model]
    return engine


async def prepare_response(results: list, embed_request: EmbeddingRequest):
    embeddings = results[0]
    usage = results[1]
    embedding_data = [
        EmbeddingData(
            object="embedding",
            embedding=emb,
            index=count,
            usage=Usage(
                prompt_tokens=usage[count],
                total_tokens=usage[count],
            ),
        )
        for count, emb in enumerate(embeddings)
    ]
    response = EmbeddingResponse(
        object="embedding",
        data=embedding_data,
        model=embed_request.model,
        id=f"textembed-{uuid4()}",
        created=int(time.time()),
    )
    return response


@embed_router.post(
    "/embedding",
    response_class=ORJSONResponse,
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(valid_token_dependency)],
)
async def create_embedding(request: Request, embed_request: EmbeddingRequest) -> EmbeddingResponse:
    engine: AsyncEngine = await get_engine(request=request, embed_request=embed_request)
    if isinstance(embed_request.input, str):
        embed_request.input = [embed_request.input]
    start_time = time.perf_counter()
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    await engine.aembed(sentences=embed_request.input, future=future)
    results = await future
    logger.info(
        "Received request with %d inputs. Processed in %.4f ms",
        len(embed_request.input),
        (time.perf_counter() - start_time) * 1000,
    )
    return await prepare_response(results=results, embed_request=embed_request)


@embed_router.post(
    "/image_embedding",
    response_class=ORJSONResponse,
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(valid_token_dependency)],
)
async def create_image_embedding(request: Request, embed_request: EmbeddingRequest) -> EmbeddingResponse:
    engine: AsyncEngine = await get_engine(request=request, embed_request=embed_request)
    if isinstance(embed_request.input, str):
        embed_request.input = [embed_request.input]
    start_time = time.perf_counter()
    image_input = [Image.open(BytesIO(base64.b64decode(image))).convert("RGB") for image in embed_request.input]
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    await engine.aembed(sentences=image_input, future=future)
    results = await future
    logger.info(
        "Received request with %d inputs. Processed in %.4f ms",
        len(embed_request.input),
        (time.perf_counter() - start_time) * 1000,
    )
    return await prepare_response(results=results, embed_request=embed_request)
