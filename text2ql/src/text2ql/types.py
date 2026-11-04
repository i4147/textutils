from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class QueryRequest:
    text: str
    target: str = "graphql"
    schema: dict[str, Any] | None = None
    mapping: dict[str, Any] | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QueryResult:
    query: str
    target: str
    confidence: float
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ValidationError(ValueError):
    def __init__(self, message: str, issues: list[str]) -> None:
        super().__init__(message)
        self.issues: list[str] = issues

    def __str__(self) -> str:
        lines = [super().__str__()]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)
