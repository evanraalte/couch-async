import json
from typing import Any, Never

import httpx

from .exceptions import (
    CouchError,
    DocumentConflictError,
    DocumentNotFoundError,
    ErrorResponse,
)
from .models import (
    AllDocsResponse,
    BulkResult,
    DatabaseInfo,
    DocumentResponse,
    FindQuery,
    FindResponse,
    FindResult,
    ViewResponse,
    ViewResult,
)


class Database:
    def __init__(self, client: httpx.AsyncClient, name: str) -> None:
        self._client = client
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> Never:
        """Centralized error handling for HTTP status codes.

        Args:
            exc: The HTTPStatusError from httpx

        Raises:
            DocumentNotFoundError: For 404 errors
            DocumentConflictError: For 409 errors
            CouchError: For other CouchDB errors
        """
        response_data = ErrorResponse.model_validate_json(exc.response.text)

        if exc.response.status_code == httpx.codes.NOT_FOUND:
            raise DocumentNotFoundError(response_data) from exc
        if exc.response.status_code == httpx.codes.CONFLICT:
            raise DocumentConflictError(response_data) from exc
        raise CouchError(response_data) from exc

    async def get_info(self) -> DatabaseInfo:
        response = await self._client.get(self._name)
        response.raise_for_status()
        return DatabaseInfo.model_validate(response.json())

    async def save(self, document: dict[str, Any]) -> DocumentResponse:
        try:
            if "_id" in document:
                response = await self._client.put(
                    f"{self._name}/{document['_id']}", json=document
                )
            else:
                response = await self._client.post(self._name, json=document)
            response.raise_for_status()
            return DocumentResponse.model_validate(response.json())
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)

    async def get(self, document_id: str, rev: str | None = None) -> dict[str, Any]:
        try:
            url = f"{self._name}/{document_id}"
            if rev:
                url = f"{url}?rev={rev}"
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)

    async def delete(self, document_id: str, rev: str) -> DocumentResponse:
        try:
            response = await self._client.delete(
                f"{self._name}/{document_id}?rev={rev}"
            )
            response.raise_for_status()
            return DocumentResponse.model_validate(response.json())
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)

    async def all_document_ids(self) -> list[str]:
        response = await self._client.get(f"{self._name}/_all_docs")
        response.raise_for_status()
        all_docs = AllDocsResponse.model_validate(response.json())
        return [row.id for row in all_docs.rows if not row.id.startswith("_design/")]

    async def bulk_save(self, documents: list[dict[str, Any]]) -> list[BulkResult]:
        response = await self._client.post(
            f"{self._name}/_bulk_docs", json={"docs": documents}
        )
        response.raise_for_status()
        results_data = response.json()
        return [BulkResult.model_validate(result) for result in results_data]

    async def find(
        self,
        selector: dict[str, Any],
        fields: list[str] | None = None,
        sort: list[dict[str, str]] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> FindResult:
        query = FindQuery(
            selector=selector, fields=fields, sort=sort, limit=limit, skip=skip
        )
        response = await self._client.post(
            f"{self._name}/_find", json=query.model_dump(exclude_none=True)
        )
        response.raise_for_status()
        result = FindResponse.model_validate(response.json())
        return FindResult(result.docs)

    async def view(
        self,
        design_doc: str,
        view_name: str,
        *,
        key: Any | None = None,
        keys: list[Any] | None = None,
        startkey: Any | None = None,
        endkey: Any | None = None,
        limit: int | None = None,
        skip: int | None = None,
        descending: bool = False,
        include_docs: bool = False,
        group: bool = False,
        reduce: bool = True,
    ) -> ViewResult:
        """Query a CouchDB view.

        Args:
            design_doc: Design document name (without _design/ prefix)
            view_name: View name within the design document
            key: Return only rows matching this key
            keys: Return only rows matching these keys (POST request)
            startkey: Start of key range
            endkey: End of key range
            limit: Limit number of results
            skip: Skip this many results
            descending: Reverse sort order
            include_docs: Include full documents in results
            group: Group results (for reduce views)
            reduce: Whether to use reduce function (default True)

        Returns:
            ViewResult with matching rows
        """
        # Build query parameters
        params: dict[str, Any] = {}
        if key is not None:
            params["key"] = json.dumps(key)
        if startkey is not None:
            params["startkey"] = json.dumps(startkey)
        if endkey is not None:
            params["endkey"] = json.dumps(endkey)
        if limit is not None:
            params["limit"] = limit
        if skip is not None:
            params["skip"] = skip
        if descending:
            params["descending"] = "true"
        if include_docs:
            params["include_docs"] = "true"
        if group:
            params["group"] = "true"
        if not reduce:
            params["reduce"] = "false"

        # Use POST with keys, or GET for other queries
        url = f"{self._name}/_design/{design_doc}/_view/{view_name}"

        if keys is not None:
            # POST request for querying multiple keys
            response = await self._client.post(url, json={"keys": keys}, params=params)
        else:
            response = await self._client.get(url, params=params)

        response.raise_for_status()
        view_response = ViewResponse.model_validate(response.json())
        return ViewResult(view_response.rows)
