import pytest

from couch import CouchClient, DatabaseAlreadyExistsError, DatabaseNotFoundError


async def test_client_can_connect(client: CouchClient) -> None:
    _ = await client.get_info()


async def test_create_database(client: CouchClient) -> None:
    _ = await client.create_database("my_db2")


async def test_create_duplicate_database_raises_error(client: CouchClient) -> None:
    await client.create_database("my_db")
    with pytest.raises(DatabaseAlreadyExistsError):
        await client.create_database("my_db")


async def test_all_databases(client: CouchClient) -> None:
    dbs = await client.all_databases()
    assert len(dbs) == 0


async def test_delete_database(client: CouchClient) -> None:
    await client.create_database("my_db3")
    await client.delete_database("my_db3")


async def test_delete_nonexistent_database_raises_error(client: CouchClient) -> None:
    with pytest.raises(DatabaseNotFoundError):
        await client.delete_database("my_db3")
