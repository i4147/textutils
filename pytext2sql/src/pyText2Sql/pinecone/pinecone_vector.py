import json
from typing import List

from pinecone import Pinecone, PodSpec, ServerlessSpec
import pandas as pd
from pyText2Sql.base import VannaBase
from pyText2Sql.utils import deterministic_uuid
from fastembed import TextEmbedding


class PineconeDB_VectorStore(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)
        if config is None:
            raise ValueError("config is required, pass either a Pinecone client or an API key in the config.")
        client = config.get("client")
        api_key = config.get("api_key")
        if not api_key and not client:
            raise ValueError("api_key is required in config or pass a configured client")
        if not client and api_key:
            self._client = Pinecone(api_key=api_key)
        elif not isinstance(client, Pinecone):
            raise ValueError("client must be an instance of Pinecone")
        else:
            self._client = client

        self.n_results = config.get("n_results", 10)
        self.dimensions = config.get("dimensions", 384)
        self.fastembed_model = config.get("fastembed_model", "BAAI/bge-small-en-v1.5")
        self.documentation_namespace = config.get("documentation_namespace", "documentation")
        self.distance_metric = config.get("distance_metric", "cosine")
        self.ddl_namespace = config.get("ddl_namespace", "ddl")
        self.sql_namespace = config.get("sql_namespace", "sql")
        self.index_name = config.get("index_name", "text2sql")
        self.metadata_config = config.get("metadata_config", {})
        self.server_type = config.get("server_type", "serverless")
        if self.server_type not in ["serverless", "pod"]:
            raise ValueError("server_type must be either 'serverless' or 'pod'")
        self.podspec = config.get(
            "podspec",
            PodSpec(
                environment="us-east-1",
                pod_type="p1.x1",
                metadata_config=self.metadata_config,
            ),
        )
        self.serverless_spec = config.get("serverless_spec", ServerlessSpec(cloud="aws", region="us-east-1"))
        self._setup_index()

    def _set_index_host(self, host: str) -> None:
        self.Index = self._client.Index(host=host)

    def _setup_index(self) -> None:
        existing_indexes = self._get_indexes()
        if self.index_name not in existing_indexes and self.server_type == "serverless":
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimensions,
                metric=self.distance_metric,
                spec=self.serverless_spec,
            )
            pinecone_index_host = self._client.describe_index(self.index_name)["host"]
            self._set_index_host(pinecone_index_host)
        elif self.index_name not in existing_indexes and self.server_type == "pod":
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimensions,
                metric=self.distance_metric,
                spec=self.podspec,
            )
            pinecone_index_host = self._client.describe_index(self.index_name)["host"]
            self._set_index_host(pinecone_index_host)
        else:
            pinecone_index_host = self._client.describe_index(self.index_name)["host"]
            self._set_index_host(pinecone_index_host)

    def _get_indexes(self) -> list:
        return [index["name"] for index in self._client.list_indexes()]

    def _check_if_embedding_exists(self, id: str, namespace: str) -> bool:
        fetch_response = self.Index.fetch(ids=[id], namespace=namespace)
        if fetch_response["vectors"] == {}:
            return False
        return True

    def add_ddl(self, ddl: str, uid: str, **kwargs) -> str:
        id = deterministic_uuid(ddl) + "-ddl"
        if self._check_if_embedding_exists(id=id, namespace=self.ddl_namespace):
            print(f"DDL with id: {id} already exists in the index. Skipping...")
            return id
        self.Index.upsert(
            vectors=[(id, self.generate_embedding(ddl), {"uid": uid})],
            namespace=self.ddl_namespace,
        )
        return id

    def add_documentation(self, doc: str, uid: str, **kwargs) -> str:
        id = deterministic_uuid(doc) + "-doc"

        if self._check_if_embedding_exists(id=id, namespace=self.documentation_namespace):
            print(f"Documentation with id: {id} already exists in the index. Skipping...")
            return id
        self.Index.upsert(
            vectors=[(id, self.generate_embedding(doc), {"uid": uid})],
            namespace=self.documentation_namespace,
        )
        return id

    def add_question_sql(self, question: str, sql: str, uid: str, **kwargs) -> str:
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        id = deterministic_uuid(question_sql_json) + "-sql"
        if self._check_if_embedding_exists(id=id, namespace=self.sql_namespace):
            print(f"Question-SQL with id: {id} already exists in the index. Skipping...")
            return id
        self.Index.upsert(
            vectors=[(id, self.generate_embedding(question_sql_json), {"uid": uid})],
            namespace=self.sql_namespace,
        )
        return id

    def get_related_ddl(self, question: str, uid: str, **kwargs) -> list:
        res = self.Index.query(
            namespace=self.ddl_namespace,
            vector=self.generate_embedding(question),
            top_k=self.n_results,
            include_values=True,
            include_metadata=True,
            filter={"uid": uid},
        )
        return (
            [
                match["metadata"]["ddl"]
                for match in res["matches"]
                if match["metadata"].get("uid") == uid and "ddl" in match["metadata"]
            ]
            if res
            else []
        )

    def get_related_documentation(self, question: str, uid: str, **kwargs) -> list:
        res = self.Index.query(
            namespace=self.documentation_namespace,
            vector=self.generate_embedding(question),
            top_k=self.n_results,
            include_values=True,
            include_metadata=True,
            filter={"uid": uid},
        )
        return [match["metadata"].get("documentation", "") for match in res["matches"]] if res else []

    def get_similar_question_sql(self, question: str, uid: str, **kwargs) -> list:
        res = self.Index.query(
            namespace=self.sql_namespace,
            vector=self.generate_embedding(question),
            top_k=self.n_results,
            include_values=True,
            include_metadata=True,
            filter={"uid": uid},
        )
        return (
            [
                {key: value for key, value in json.loads(match["metadata"]["sql"]).items()}
                for match in res["matches"]
                if "sql" in match["metadata"] and match["metadata"]["uid"] == uid
            ]
            if res
            else []
        )

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        df = pd.DataFrame()
        namespaces = {
            "sql": self.sql_namespace,
            "ddl": self.ddl_namespace,
            "documentation": self.documentation_namespace,
        }

        for data_type, namespace in namespaces.items():
            data = self.Index.query(
                top_k=10000,
                namespace=namespace,
                include_values=True,
                include_metadata=True,
                vector=[0.0] * self.dimensions,
            )

            if data is not None:
                id_list = [match["id"] for match in data["matches"]]
                content_list = [match["metadata"][data_type] for match in data["matches"]]
                question_list = [
                    (json.loads(match["metadata"][data_type])["question"] if data_type == "sql" else None)
                    for match in data["matches"]
                ]

                df_data = pd.DataFrame({
                    "id": id_list,
                    "question": question_list,
                    "content": content_list,
                })
                df_data["training_data_type"] = data_type
                df = pd.concat([df, df_data])

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.Index.delete(ids=[id], namespace=self.sql_namespace)
            return True
        elif id.endswith("-ddl"):
            self.Index.delete(ids=[id], namespace=self.ddl_namespace)
            return True
        elif id.endswith("-doc"):
            self.Index.delete(ids=[id], namespace=self.documentation_namespace)
            return True
        else:
            return False

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding_model = TextEmbedding(model_name=self.fastembed_model)
        embedding = next(embedding_model.embed(data))
        return embedding.tolist()
