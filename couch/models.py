from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel


class ServerInfo(BaseModel):
    couchdb: str
    version: str
    git_sha: str
    uuid: str
    features: list[str]


class DatabaseInfo(BaseModel):
    db_name: str
    doc_count: int
    doc_del_count: int
    update_seq: str | int
    purge_seq: str | int | None = None
    compact_running: bool
    disk_size: int | None = None
    data_size: int | None = None
    instance_start_time: str
    disk_format_version: int
    committed_update_seq: str | int | None = None
    sizes: dict[str, Any] | None = None


class DocumentResponse(BaseModel):
    ok: bool
    id: str
    rev: str


class AllDocsRow(BaseModel):
    id: str
    key: str
    value: dict[str, str]
    doc: dict[str, Any] | None = None


class AllDocsResponse(BaseModel):
    total_rows: int
    offset: int
    rows: list[AllDocsRow]


class BulkResult(BaseModel):
    ok: bool | None = None
    id: str
    rev: str | None = None
    error: str | None = None
    reason: str | None = None


class FindQuery(BaseModel):
    selector: dict[str, Any]
    fields: list[str] | None = None
    sort: list[dict[str, str]] | None = None
    limit: int | None = None
    skip: int | None = None
    use_index: str | list[str] | None = None


class FindResponse(BaseModel):
    docs: list[dict[str, Any]]
    bookmark: str | None = None
    warning: str | None = None
    execution_stats: dict[str, Any] | None = None


class FindResult:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._docs)

    def __len__(self) -> int:
        return len(self._docs)


class ViewRow(BaseModel):
    id: str | None = None  # Not present in reduce views
    key: Any
    value: Any
    doc: dict[str, Any] | None = None


class ViewResponse(BaseModel):
    total_rows: int | None = None  # Not present in reduce views
    offset: int | None = None  # Not present in reduce views
    rows: list[ViewRow]


class ViewResult:
    """Iterable wrapper for view results with convenience methods."""

    def __init__(self, rows: list[ViewRow]) -> None:
        self._rows = rows

    def __iter__(self) -> Iterator[ViewRow]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    def keys(self) -> list[Any]:
        """Extract all keys from view results."""
        return [row.key for row in self._rows]

    def values(self) -> list[Any]:
        """Extract all values from view results."""
        return [row.value for row in self._rows]

    def docs(self) -> list[dict[str, Any]]:
        """Extract all documents (requires include_docs=true)."""
        return [row.doc for row in self._rows if row.doc is not None]
