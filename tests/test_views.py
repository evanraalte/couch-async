from couch import Database


async def test_view_with_map_only(db: Database) -> None:
    # Create design doc with map view
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    # Add test documents
    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25},
            {"_id": "user2", "name": "Bob", "age": 35},
            {"_id": "user3", "name": "Charlie", "age": 30},
        ]
    )

    # Query view
    results = await db.view("users", "by_age")
    assert len(results) == 3
    assert results.keys() == [25, 30, 35]  # Sorted by key
    assert results.values() == ["Alice", "Charlie", "Bob"]


async def test_view_with_key_range(db: Database) -> None:
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25},
            {"_id": "user2", "name": "Bob", "age": 35},
            {"_id": "user3", "name": "Charlie", "age": 30},
            {"_id": "user4", "name": "Dave", "age": 45},
        ]
    )

    # Query with key range
    results = await db.view("users", "by_age", startkey=25, endkey=32)
    assert len(results) == 2
    assert results.keys() == [25, 30]


async def test_view_with_include_docs(db: Database) -> None:
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25, "email": "alice@example.com"},
            {"_id": "user2", "name": "Bob", "age": 35, "email": "bob@example.com"},
        ]
    )

    # Query with include_docs
    results = await db.view("users", "by_age", include_docs=True)
    docs = results.docs()
    assert len(docs) == 2
    assert all("email" in doc for doc in docs)
    assert docs[0]["name"] == "Alice"


async def test_view_with_specific_key(db: Database) -> None:
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25},
            {"_id": "user2", "name": "Bob", "age": 35},
            {"_id": "user3", "name": "Charlie", "age": 25},
        ]
    )

    # Query with specific key
    results = await db.view("users", "by_age", key=25)
    assert len(results) == 2
    assert all(row.key == 25 for row in results)


async def test_view_with_limit_and_skip(db: Database) -> None:
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25},
            {"_id": "user2", "name": "Bob", "age": 30},
            {"_id": "user3", "name": "Charlie", "age": 35},
            {"_id": "user4", "name": "Dave", "age": 40},
            {"_id": "user5", "name": "Eve", "age": 45},
        ]
    )

    # Query with limit and skip
    results = await db.view("users", "by_age", skip=1, limit=3)
    assert len(results) == 3
    assert results.keys() == [30, 35, 40]


async def test_view_with_descending_order(db: Database) -> None:
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25},
            {"_id": "user2", "name": "Bob", "age": 35},
            {"_id": "user3", "name": "Charlie", "age": 30},
        ]
    )

    # Query in descending order
    results = await db.view("users", "by_age", descending=True)
    assert len(results) == 3
    assert results.keys() == [35, 30, 25]


async def test_view_with_map_reduce(db: Database) -> None:
    design_doc = {
        "_id": "_design/stats",
        "views": {
            "count_by_status": {
                "map": "function(doc) { if (doc.status) emit(doc.status, 1); }",
                "reduce": "_count",
            }
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "task1", "status": "active"},
            {"_id": "task2", "status": "active"},
            {"_id": "task3", "status": "completed"},
            {"_id": "task4", "status": "active"},
        ]
    )

    # Query with reduce
    results = await db.view("stats", "count_by_status", group=True)
    assert len(results) == 2
    # Results should be grouped by status with counts
    keys = results.keys()
    values = results.values()
    assert "active" in keys
    assert "completed" in keys
    # Find the count for active
    active_idx = keys.index("active")
    assert values[active_idx] == 3


async def test_view_with_keys_parameter(db: Database) -> None:
    design_doc = {
        "_id": "_design/users",
        "views": {
            "by_age": {"map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"}
        },
    }
    await db.save(design_doc)

    await db.bulk_save(
        [
            {"_id": "user1", "name": "Alice", "age": 25},
            {"_id": "user2", "name": "Bob", "age": 30},
            {"_id": "user3", "name": "Charlie", "age": 35},
            {"_id": "user4", "name": "Dave", "age": 40},
        ]
    )

    # Query with multiple specific keys
    results = await db.view("users", "by_age", keys=[25, 35])
    assert len(results) == 2
    assert results.keys() == [25, 35]
    assert results.values() == ["Alice", "Charlie"]
