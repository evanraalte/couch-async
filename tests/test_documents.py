import pytest

from couch import (
    Database,
    DocumentConflictError,
    DocumentNotFoundError,
    DocumentResponse,
)


async def test_save_document_without_id_generates_id(db: Database) -> None:
    doc = {"type": "user", "name": "Alice"}
    response = await db.save(doc)

    assert isinstance(response, DocumentResponse)
    assert response.ok is True
    assert len(response.id) > 0
    assert len(response.rev) > 0
    assert response.rev.startswith("1-")


async def test_save_document_with_id_uses_id(db: Database) -> None:
    doc = {"_id": "user123", "name": "Bob"}
    response = await db.save(doc)

    assert response.id == "user123"
    assert response.ok is True
    assert response.rev.startswith("1-")


async def test_update_document_with_rev_succeeds(db: Database) -> None:
    doc = {"_id": "user123", "name": "Bob"}
    r1 = await db.save(doc)

    doc["_rev"] = r1.rev
    doc["name"] = "Robert"
    r2 = await db.save(doc)

    assert r2.ok is True
    assert r2.rev.startswith("2-")
    assert r2.rev != r1.rev


async def test_update_document_without_rev_raises_conflict(db: Database) -> None:
    doc = {"_id": "user123", "name": "Bob"}
    await db.save(doc)

    doc["name"] = "Robert"
    with pytest.raises(DocumentConflictError):
        await db.save(doc)


async def test_get_document_by_id_returns_document(db: Database) -> None:
    doc = {"_id": "user123", "name": "Alice", "age": 30}
    saved = await db.save(doc)

    retrieved = await db.get("user123")

    assert retrieved["_id"] == "user123"
    assert retrieved["_rev"] == saved.rev
    assert retrieved["name"] == "Alice"
    assert retrieved["age"] == 30


async def test_get_nonexistent_document_raises_error(db: Database) -> None:
    with pytest.raises(DocumentNotFoundError):
        await db.get("nonexistent")


async def test_delete_document_with_rev_succeeds(db: Database) -> None:
    doc = {"_id": "user123", "name": "Alice"}
    saved = await db.save(doc)

    response = await db.delete("user123", saved.rev)

    assert response.ok is True
    assert response.id == "user123"

    with pytest.raises(DocumentNotFoundError):
        await db.get("user123")


async def test_delete_with_wrong_rev_raises_conflict(db: Database) -> None:
    doc = {"_id": "user123", "name": "Alice"}
    await db.save(doc)

    with pytest.raises(DocumentConflictError):
        await db.delete("user123", "1-fakerevisionnumber")


async def test_delete_nonexistent_document_raises_error(db: Database) -> None:
    with pytest.raises(DocumentNotFoundError):
        await db.delete("nonexistent", "1-abc")


async def test_all_document_ids_returns_list_of_ids(db: Database) -> None:
    await db.save({"_id": "doc1", "data": "a"})
    await db.save({"_id": "doc2", "data": "b"})
    await db.save({"_id": "doc3", "data": "c"})

    ids = await db.all_document_ids()

    assert len(ids) == 3
    assert "doc1" in ids
    assert "doc2" in ids
    assert "doc3" in ids


async def test_all_document_ids_excludes_design_docs(db: Database) -> None:
    await db.save({"_id": "doc1", "data": "a"})
    await db.save({"_id": "_design/myview", "views": {}})

    ids = await db.all_document_ids()

    assert len(ids) == 1
    assert "doc1" in ids
    assert "_design/myview" not in ids
