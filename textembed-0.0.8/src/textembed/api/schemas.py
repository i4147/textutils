import time
from typing import List, Literal, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    payload: Optional[Union[str, int, float, dict, list]] = None
    message: Optional[str] = None
    code: Optional[int] = None


class Root(BaseModel):
    payload: Optional[Union[str, int, float, dict, list]] = None
    message: Optional[str] = None
    code: Optional[int] = None


class ModelDetails(BaseModel):
    id: str
    served_model_name: str
    object: str = "model"
    owned_by: str = "textembed"
    created: int = Field(default_factory=lambda: int(time.time()))


class ModelList(BaseModel):
    data: List[ModelDetails]
    object: str = "list"


class EmbeddingRequest(BaseModel):
    input: List[str]
    model: str
    user: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int | str
    total_tokens: int | str


class EmbeddingData(BaseModel):
    object: Literal["embedding"] = "embedding"
    embedding: List[Union[float, int]]
    usage: Usage
    index: int


class EmbeddingResponse(BaseModel):
    object: Literal["embedding"] = "embedding"
    data: List[EmbeddingData]
    model: str
    id: str = Field(default_factory=lambda: f"textembed-{uuid4()}")
    created: int = Field(default_factory=lambda: int(time.time()))
