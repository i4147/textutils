import os.path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PDFTEXT_")

    WORKER_PAGE_THRESHOLD: int = 10

    RESULTS_FOLDER: str = "results"
    BENCH_DATASET_NAME: str = "vikp/pdf_bench"


settings = Settings()
