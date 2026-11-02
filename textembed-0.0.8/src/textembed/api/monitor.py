import time
from fastapi import APIRouter, Response
from prometheus_client import REGISTRY, generate_latest
from textembed.api.schemas import HealthCheck, Root

monitor_router = APIRouter(tags=["Monitor"])


@monitor_router.get("/")
async def _root() -> Root:
    return Root(
        payload=None,
        message="TextEmbed service.",
        code=200,
    )


@monitor_router.get("/health")
async def _health() -> HealthCheck:
    return HealthCheck(
        payload={"unix": int(time.time())},
        message="Health check done",
        code=200,
    )


@monitor_router.get("/metrics")
async def metrics() -> Response:
    metrics_str = generate_latest(REGISTRY)
    return Response(content=metrics_str, media_type="text/plain")
