from couch import Database


async def test_bulk_save_inserts_multiple_documents(db: Database) -> None:
    docs = [
        {"_id": "user1", "name": "Alice"},
        {"_id": "user2", "name": "Bob"},
        {"_id": "user3", "name": "Charlie"},
    ]

    results = await db.bulk_save(docs)

    assert len(results) == 3
    for result in results:
        assert result.ok is True
        assert result.id in ["user1", "user2", "user3"]
        assert result.rev is not None
        assert result.rev.startswith("1-")


async def test_bulk_save_updates_existing_documents(db: Database) -> None:
    docs = [{"_id": "user1", "name": "Alice"}, {"_id": "user2", "name": "Bob"}]
    initial_results = await db.bulk_save(docs)

    updates = [
        {"_id": "user1", "_rev": initial_results[0].rev, "name": "Alice Updated"},
        {"_id": "user2", "_rev": initial_results[1].rev, "name": "Bob Updated"},
    ]

    results = await db.bulk_save(updates)

    assert len(results) == 2
    assert results[0].ok is True
    assert results[0].rev is not None
    assert results[0].rev.startswith("2-")
    assert results[1].ok is True
    assert results[1].rev is not None
    assert results[1].rev.startswith("2-")


async def test_bulk_save_reports_individual_failures(db: Database) -> None:
    await db.save({"_id": "user1", "name": "Alice"})

    docs = [
        {"_id": "user1", "_rev": "1-badrevision", "name": "Alice Updated"},
        {"_id": "user2", "name": "Bob"},
    ]

    results = await db.bulk_save(docs)

    assert len(results) == 2
    assert results[0].error == "conflict"
    assert results[0].ok is None
    assert results[1].ok is True
    assert results[1].error is None


async def test_bulk_save_auto_generates_ids(db: Database) -> None:
    docs = [{"name": "Alice"}, {"name": "Bob"}]

    results = await db.bulk_save(docs)

    assert len(results) == 2
    assert results[0].ok is True
    assert len(results[0].id) > 0
    assert results[1].ok is True
    assert len(results[1].id) > 0
    assert results[0].id != results[1].id
