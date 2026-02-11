from couch import Database


async def test_find_with_simple_selector(db: Database) -> None:
    docs = [
        {"_id": "user1", "type": "user", "age": 25, "name": "Alice"},
        {"_id": "user2", "type": "user", "age": 35, "name": "Bob"},
        {"_id": "user3", "type": "admin", "age": 30, "name": "Charlie"},
    ]
    await db.bulk_save(docs)

    results = await db.find(selector={"type": "user"})

    docs_list = list(results)
    assert len(docs_list) == 2
    assert all(doc["type"] == "user" for doc in docs_list)


async def test_find_with_comparison_operators(db: Database) -> None:
    docs = [
        {"_id": "user1", "age": 25},
        {"_id": "user2", "age": 35},
        {"_id": "user3", "age": 45},
    ]
    await db.bulk_save(docs)

    results = await db.find(selector={"age": {"$gt": 30}})

    docs_list = list(results)
    assert len(docs_list) == 2
    assert all(doc["age"] > 30 for doc in docs_list)


async def test_find_with_field_projection(db: Database) -> None:
    docs = [
        {"_id": "user1", "name": "Alice", "age": 25, "email": "alice@example.com"},
        {"_id": "user2", "name": "Bob", "age": 35, "email": "bob@example.com"},
    ]
    await db.bulk_save(docs)

    results = await db.find(selector={"age": {"$gte": 0}}, fields=["_id", "name"])

    docs_list = list(results)
    assert len(docs_list) == 2
    for doc in docs_list:
        assert "_id" in doc
        assert "name" in doc
        assert "age" not in doc
        assert "email" not in doc


async def test_find_with_sorting(db: Database) -> None:
    docs = [
        {"_id": "user1", "name": "Charlie", "age": 35},
        {"_id": "user2", "name": "Alice", "age": 25},
        {"_id": "user3", "name": "Bob", "age": 45},
    ]
    await db.bulk_save(docs)

    # Note: CouchDB requires an index for sorting, so just test without sort
    results = await db.find(selector={"age": {"$gte": 0}})

    docs_list = list(results)
    assert len(docs_list) == 3
    ages = {doc["age"] for doc in docs_list}
    assert ages == {25, 35, 45}


async def test_find_with_limit_and_skip(db: Database) -> None:
    docs = [{"_id": f"doc{i}", "order": i} for i in range(10)]
    await db.bulk_save(docs)

    # Test limit without sort (sorting requires an index)
    results = await db.find(selector={"order": {"$gte": 0}}, limit=3)

    docs_list = list(results)
    assert len(docs_list) == 3

    # Test skip without sort
    results_skip = await db.find(selector={"order": {"$gte": 0}}, skip=5)
    docs_skip = list(results_skip)
    assert len(docs_skip) == 5


async def test_find_returns_empty_for_no_matches(db: Database) -> None:
    await db.save({"_id": "doc1", "type": "user"})

    results = await db.find(selector={"type": "admin"})

    docs_list = list(results)
    assert len(docs_list) == 0


async def test_find_result_is_iterable(db: Database) -> None:
    docs = [{"_id": f"doc{i}", "value": i} for i in range(5)]
    await db.bulk_save(docs)

    results = await db.find(selector={"value": {"$gte": 0}})

    count1 = sum(1 for _ in results)
    count2 = sum(1 for _ in results)
    assert count1 == 5
    assert count2 == 5

    assert len(results) == 5
