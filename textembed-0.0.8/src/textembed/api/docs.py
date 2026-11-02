import textembed

FASTAPI_TITLE = "TextEmbed - Embedding Inference Server"
FASTAPI_SUMMARY = (
    "TextEmbed is a REST API designed for high-throughput and low-latency vector embedding "
    "services. It supports a wide array of sentence-transformer models and frameworks, "
    "making it suitable for diverse applications in natural language processing."
)
FASTAPI_DESCRIPTION = (
    "TextEmbed provides a robust and scalable REST API for generating vector embeddings from text. "
    "Built for performance and flexibility, it supports various sentence-transformer models, allowing "
    "users to easily integrate state-of-the-art NLP techniques into their applications. Whether you need "
    "embeddings for search, recommendation, or other NLP tasks, TextEmbed delivers with high efficiency."
)


def startup_message(host: str, port: str) -> str:
    return f"""
TextEmbed - Embedding Inference Server
Apache License 2: Copyright (c) 2024 Keval Dekivadiya
Version {textembed.__version__}

Open the Docs via Swagger UI:
http://{host}:{port}/docs
"""
