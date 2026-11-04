from functools import cached_property
from typing import List, Tuple

import pandas as pd
from qdrant_client import QdrantClient, grpc, models
from qdrant_client.http.models.models import UpdateStatus

from ..base import VannaBase
from ..utils import deterministic_uuid

SCROLL_SIZE = 1000


class Qdrant_VectorStore(VannaBase):
    def __init__(
        self,
        config={},
    ):
        VannaBase.__init__(self, config=config)
        client = config.get("client")

        if client is None:
            self._client = QdrantClient(
                location=config.get("location", None),
                url=config.get("url", None),
                prefer_grpc=config.get("prefer_grpc", False),
                https=config.get("https", None),
                api_key=config.get("api_key", None),
                timeout=config.get("timeout", None),
                path=config.get("path", None),
                prefix=config.get("prefix", None),
            )
        elif not isinstance(client, QdrantClient):
            raise TypeError(f"Unsupported client of type {client.__class__} was set in config")

        else:
            self._client = client

        self.n_results = config.get("n_results", 10)
        self.fastembed_model = config.get("fastembed_model", "BAAI/bge-small-en-v1.5")
        self.collection_params = config.get("collection_params", {})
        self.distance_metric = config.get("distance_metric", models.Distance.COSINE)
        self.documentation_collection_name = config.get("documentation_collection_name", "documentation")
        self.ddl_collection_name = config.get("ddl_collection_name", "ddl")
        self.sql_collection_name = config.get("sql_collection_name", "sql")

        self.id_suffixes = {
            self.ddl_collection_name: "ddl",
            self.documentation_collection_name: "doc",
            self.sql_collection_name: "sql",
        }

        self._setup_collections()

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        question_answer = "Question: {0}\n\nSQL: {1}".format(question, sql)
        id = deterministic_uuid(question_answer)

        self._client.upsert(
            self.sql_collection_name,
            points=[
                models.PointStruct(
                    id=id,
                    vector=self.generate_embedding(question_answer),
                    payload={
                        "question": question,
                        "sql": sql,
                    },
                )
            ],
        )

        return self._format_point_id(id, self.sql_collection_name)

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = deterministic_uuid(ddl)
        self._client.upsert(
            self.ddl_collection_name,
            points=[
                models.PointStruct(
                    id=id,
                    vector=self.generate_embedding(ddl),
                    payload={
                        "ddl": ddl,
                    },
                )
            ],
        )
        return self._format_point_id(id, self.ddl_collection_name)

    def add_documentation(self, documentation: str, **kwargs) -> str:
        id = deterministic_uuid(documentation)

        self._client.upsert(
            self.documentation_collection_name,
            points=[
                models.PointStruct(
                    id=id,
                    vector=self.generate_embedding(documentation),
                    payload={
                        "documentation": documentation,
                    },
                )
            ],
        )

        return self._format_point_id(id, self.documentation_collection_name)

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        df = pd.DataFrame()

        if sql_data := self._get_all_points(self.sql_collection_name):
            question_list = [data.payload["question"] for data in sql_data]
            sql_list = [data.payload["sql"] for data in sql_data]
            id_list = [self._format_point_id(data.id, self.sql_collection_name) for data in sql_data]

            df_sql = pd.DataFrame({
                "id": id_list,
                "question": question_list,
                "content": sql_list,
            })

            df_sql["training_data_type"] = "sql"

            df = pd.concat([df, df_sql])

        if ddl_data := self._get_all_points(self.ddl_collection_name):
            ddl_list = [data.payload["ddl"] for data in ddl_data]
            id_list = [self._format_point_id(data.id, self.ddl_collection_name) for data in ddl_data]

            df_ddl = pd.DataFrame({
                "id": id_list,
                "question": [None for _ in ddl_list],
                "content": ddl_list,
            })

            df_ddl["training_data_type"] = "ddl"

            df = pd.concat([df, df_ddl])

        if doc_data := self._get_all_points(self.documentation_collection_name):
            document_list = [data.payload["documentation"] for data in doc_data]
            id_list = [self._format_point_id(data.id, self.documentation_collection_name) for data in doc_data]

            df_doc = pd.DataFrame({
                "id": id_list,
                "question": [None for _ in document_list],
                "content": document_list,
            })

            df_doc["training_data_type"] = "documentation"

            df = pd.concat([df, df_doc])

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        try:
            id, collection_name = self._parse_point_id(id)
            res = self._client.delete(collection_name, points_selector=[id])
            return True
        except ValueError:
            return False

    def remove_collection(self, collection_name: str) -> bool:
        if collection_name in self.id_suffixes.keys():
            self._client.delete_collection(collection_name)
            self._setup_collections()
            return True
        else:
            return False

    @cached_property
    def embeddings_dimension(self):
        return len(self.generate_embedding("ABCDEF"))

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        results = self._client.search(
            self.sql_collection_name,
            query_vector=self.generate_embedding(question),
            limit=self.n_results,
            with_payload=True,
        )

        return [dict(result.payload) for result in results]

    def get_related_ddl(self, question: str, **kwargs) -> list:
        results = self._client.search(
            self.ddl_collection_name,
            query_vector=self.generate_embedding(question),
            limit=self.n_results,
            with_payload=True,
        )

        return [result.payload["ddl"] for result in results]

    def get_related_documentation(self, question: str, **kwargs) -> list:
        results = self._client.search(
            self.documentation_collection_name,
            query_vector=self.generate_embedding(question),
            limit=self.n_results,
            with_payload=True,
        )

        return [result.payload["documentation"] for result in results]

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding_model = self._client._get_or_init_model(model_name=self.fastembed_model)
        embedding = next(embedding_model.embed(data))

        return embedding.tolist()

    def _get_all_points(self, collection_name: str):
        results: List[models.Record] = []
        next_offset = None
        stop_scrolling = False
        while not stop_scrolling:
            records, next_offset = self._client.scroll(
                collection_name,
                limit=SCROLL_SIZE,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            stop_scrolling = next_offset is None or (
                isinstance(next_offset, grpc.PointId) and next_offset.num == 0 and next_offset.uuid == ""
            )

            results.extend(records)

        return results

    def _setup_collections(self):
        if not self._client.collection_exists(self.sql_collection_name):
            self._client.create_collection(
                collection_name=self.sql_collection_name,
                vectors_config=models.VectorParams(
                    size=self.embeddings_dimension,
                    distance=self.distance_metric,
                ),
                **self.collection_params,
            )

        if not self._client.collection_exists(self.ddl_collection_name):
            self._client.create_collection(
                collection_name=self.ddl_collection_name,
                vectors_config=models.VectorParams(
                    size=self.embeddings_dimension,
                    distance=self.distance_metric,
                ),
                **self.collection_params,
            )
        if not self._client.collection_exists(self.documentation_collection_name):
            self._client.create_collection(
                collection_name=self.documentation_collection_name,
                vectors_config=models.VectorParams(
                    size=self.embeddings_dimension,
                    distance=self.distance_metric,
                ),
                **self.collection_params,
            )

    def _format_point_id(self, id: str, collection_name: str) -> str:
        return "{0}-{1}".format(id, self.id_suffixes[collection_name])

    def _parse_point_id(self, id: str) -> Tuple[str, str]:
        id, curr_suffix = id.rsplit("-", 1)
        for collection_name, suffix in self.id_suffixes.items():
            if curr_suffix == suffix:
                return id, collection_name
        raise ValueError(f"Invalid id {id}")
