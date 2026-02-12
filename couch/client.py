from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from .config import CouchConfig
from .database import Database
from .exceptions import (
    DatabaseAlreadyExistsError,
    DatabaseNotFoundError,
    ErrorResponse,
)
from .models import ServerInfo


class CouchClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_info(self) -> ServerInfo:
        response = await self._client.get("")
        response.raise_for_status()
        return ServerInfo.model_validate(response.json())

    async def create_database(self, name: str) -> None:
        try:
            response = await self._client.put(name)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            rsp = ErrorResponse.model_validate_json(exc.response.text)
            raise DatabaseAlreadyExistsError(rsp) from exc

    async def all_databases(self) -> list[str]:
        response = await self._client.get("_all_dbs")
        response.raise_for_status()
        return [db for db in response.json() if not db.startswith("_")]

    async def delete_database(self, name: str) -> None:
        try:
            response = await self._client.delete(name)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            rsp = ErrorResponse.model_validate_json(exc.response.text)
            raise DatabaseNotFoundError(rsp) from exc

    def database(self, name: str) -> Database:
        return Database(self._client, name)

    async def database_exists(self, name: str) -> bool:
        try:
            response = await self._client.head(name)
        except httpx.HTTPStatusError:
            return False
        else:
            return response.status_code == httpx.codes.OK


@asynccontextmanager
async def connect(config: CouchConfig) -> AsyncIterator[CouchClient]:
    """Create a CouchClient with properly configured HTTP client."""
    async with httpx.AsyncClient(
        auth=httpx.BasicAuth(
            username=config.username, password=config.password.get_secret_value()
        ),
        base_url=config.url,
        http2=True,
        verify=config.verify_ssl,
    ) as http_client:
        yield CouchClient(http_client)
