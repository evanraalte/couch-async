from couch import CouchClient, Database, DatabaseInfo


async def test_database_returns_database_instance(client: CouchClient) -> None:
    await client.create_database("test_db")
    db = client.database("test_db")
    assert isinstance(db, Database)
    assert db.name == "test_db"


async def test_database_info_returns_metadata(client: CouchClient) -> None:
    await client.create_database("test_db")
    db = client.database("test_db")
    info = await db.get_info()
    assert isinstance(info, DatabaseInfo)
    assert info.db_name == "test_db"
    assert info.doc_count == 0
    assert info.sizes is not None
    assert isinstance(info.sizes["file"], int)
    assert isinstance(info.sizes["active"], int)


async def test_database_exists_returns_true_for_existing_db(
    client: CouchClient,
) -> None:
    await client.create_database("test_db")
    exists = await client.database_exists("test_db")
    assert exists is True


async def test_database_exists_returns_false_for_missing_db(
    client: CouchClient,
) -> None:
    exists = await client.database_exists("nonexistent")
    assert exists is False
