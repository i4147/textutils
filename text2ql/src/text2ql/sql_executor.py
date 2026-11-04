from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from text2ql.dataset import DatasetExample

logger = logging.getLogger(__name__)

_SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None


def _require_sqlalchemy() -> None:
    if not _SQLALCHEMY_AVAILABLE:
        raise ImportError(
            "SQLAlchemy is required for SQL execution. "
            "Install it with: pip install text2ql[sql]  "
            "or: pip install 'sqlalchemy>=2.0'"
        )


def _sqlalchemy_module() -> Any:
    _require_sqlalchemy()
    try:
        return importlib.import_module("sqlalchemy")
    except ImportError as exc:
        raise ImportError(
            "SQLAlchemy is required for SQL execution. "
            "Install it with: pip install text2ql[sql]  "
            "or: pip install 'sqlalchemy>=2.0'"
        ) from exc


class SQLAlchemyExecutor:
    def __init__(
        self,
        engine_or_url: Any,
        connect_args: dict[str, Any] | None = None,
        row_limit: int | None = 10_000,
    ) -> None:
        sa = _sqlalchemy_module()

        if isinstance(engine_or_url, str):
            kwargs: dict[str, Any] = {}
            if connect_args:
                kwargs["connect_args"] = connect_args
            self._engine = sa.create_engine(engine_or_url, **kwargs)
            logger.debug("Created SQLAlchemy engine from URL: %s", engine_or_url)
        else:
            self._engine = engine_or_url
            logger.debug("Using provided SQLAlchemy engine: %s", engine_or_url)

        self._row_limit = row_limit

    def execute(self, sql: str) -> list[dict[str, Any]]:
        sa = _sqlalchemy_module()

        statement = _maybe_add_limit(sql, self._row_limit)
        logger.debug("Executing SQL: %s", statement)
        with self._engine.connect() as conn:
            result = conn.execute(sa.text(statement))
            keys = list(result.keys())
            rows = [dict(zip(keys, row)) for row in result.fetchall()]
        logger.debug("SQL returned %d row(s)", len(rows))
        return rows

    async def aexecute(self, sql: str) -> list[dict[str, Any]]:
        import asyncio

        return await asyncio.to_thread(self.execute, sql)

    def __call__(self, sql: str, example: "DatasetExample") -> list[dict[str, Any]]:
        return self.execute(sql)

    def load_json_data(
        self,
        table_name: str,
        rows: list[dict[str, Any]],
        if_exists: str = "replace",
    ) -> None:
        if not rows:
            logger.warning("load_json_data: no rows provided for table '%s'", table_name)
            return

        try:
            import pandas as pd

            df = pd.DataFrame(rows)
            df.to_sql(table_name, con=self._engine, if_exists=if_exists, index=False)
            logger.debug("Loaded %d rows into '%s' via pandas", len(rows), table_name)
        except ImportError:
            _load_json_data_raw(self._engine, table_name, rows)
            logger.debug("Loaded %d rows into '%s' via raw DDL", len(rows), table_name)

    def dispose(self) -> None:
        self._engine.dispose()
        logger.debug("Disposed SQLAlchemy engine")

    def __enter__(self) -> "SQLAlchemyExecutor":
        return self

    def __exit__(self, *_: Any) -> None:
        self.dispose()


def create_sqlite_executor(
    rows_by_table: dict[str, list[dict[str, Any]]] | None = None,
    row_limit: int | None = 10_000,
) -> SQLAlchemyExecutor:
    sa = _sqlalchemy_module()

    engine = sa.create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    executor = SQLAlchemyExecutor(engine, row_limit=row_limit)

    if rows_by_table:
        for table_name, rows in rows_by_table.items():
            executor.load_json_data(table_name, rows)

    return executor


def _maybe_add_limit(sql: str, row_limit: int | None) -> str:
    if row_limit is None:
        return sql
    normalized = sql.strip().upper()
    if "LIMIT" in normalized:
        return sql
    stripped = sql.rstrip().rstrip(";")
    return f"{stripped} LIMIT {row_limit};"


def _load_json_data_raw(engine: Any, table_name: str, rows: list[dict[str, Any]]) -> None:
    sa = _sqlalchemy_module()

    columns = list(rows[0].keys())
    col_defs = ", ".join(f'"{col}" TEXT' for col in columns)
    with engine.begin() as conn:
        conn.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}"'))
        conn.execute(sa.text(f'CREATE TABLE "{table_name}" ({col_defs})'))
        placeholders = ", ".join(f":{col}" for col in columns)
        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
        for row in rows:
            conn.execute(sa.text(insert_sql), row)
