"""Shared pytest fixtures for all test files."""

from collections.abc import AsyncGenerator

import pytest

from couch import CouchClient, CouchConfig, Database, connect


@pytest.fixture
async def client() -> AsyncGenerator[CouchClient]:
    """Create a CouchDB client and clean up all databases after tests."""
    config = CouchConfig(
        url="http://localhost:5984",
        username="admin",
        password="password",  # type:ignore[arg-type]
    )

    async with connect(config) as client:
        yield client
        # Cleanup: delete all non-system databases after each test
        dbs = await client.all_databases()
        for db in dbs:
            await client.delete_database(db)


@pytest.fixture
async def db(client: CouchClient) -> Database:
    """Create a test database."""
    await client.create_database("test_db")
    return client.database("test_db")
