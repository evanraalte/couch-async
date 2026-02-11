# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Python async HTTP/2 client library for CouchDB 3.x with type-safe interfaces using httpx and Pydantic.

**Tech Stack**: Python 3.13+, httpx (HTTP/2), Pydantic, pytest-asyncio

## Common Commands

```bash
# Tests
uv run pytest -vvv                    # Run all tests
uv run pytest tests/test_views.py -vvv  # Run specific test file

# Linting
uv run ruff check --fix               # Lint and auto-fix
make check                            # Run all checks (lint + tests)

# CouchDB (Docker)
docker compose up -d                  # Start CouchDB
docker compose logs -f couchdb        # View logs
```

**CouchDB Access**: http://localhost:5984 (admin/password)

## Architecture

### File Structure
```
couch/
├── __init__.py      # Public API exports
├── config.py        # CouchConfig settings
├── client.py        # CouchClient, connect()
├── database.py      # Database class
├── models.py        # Pydantic models for all CouchDB responses
└── exceptions.py    # Exception hierarchy

tests/               # 40 tests across 6 files
```

### Core Classes

**CouchClient** (`couch/client.py`) - Server-level operations
- `get_info()` - Server information
- `create_database(name)` - Create database
- `all_databases()` - List databases (excludes system DBs)
- `delete_database(name)` - Delete database
- `database(name)` - Get Database instance
- `database_exists(name)` - Check existence

**Database** (`couch/database.py`) - Database-level operations
- `get_info()` - Database metadata
- `save(document)` - Create/update documents (auto-generates _id if missing)
- `get(document_id, rev=None)` - Retrieve document
- `delete(document_id, rev)` - Delete document
- `all_document_ids()` - List all doc IDs (excludes design docs)
- `bulk_save(documents)` - Bulk insert/update
- `find(selector, fields, limit, skip)` - Mango queries
- `view(design_doc, view_name, **params)` - CouchDB views

**Context Manager**: `connect(config)` - AsyncContextManager with HTTP/2 client

### Models (couch/models.py)

Response models: `ServerInfo`, `DatabaseInfo`, `DocumentResponse`, `AllDocsResponse`, `BulkResult`, `FindResponse`, `ViewResponse`

Wrapper classes: `FindResult` (Mango), `ViewResult` (Views with `keys()`, `values()`, `docs()` methods)

### Exceptions (couch/exceptions.py)

- `CouchError` - Base exception
- `DatabaseAlreadyExistsError` / `DatabaseNotFoundError` - Database operations
- `DocumentNotFoundError` (404) / `DocumentConflictError` (409) - Document operations

### Error Handling

Database class uses centralized `_handle_http_error()` method (couch/database.py) to map HTTP status codes to appropriate exceptions.

## Features

**Server Operations** ✅
- Server info, database CRUD, database listing

**Document Operations** ✅
- Save (with/without _id), get, delete, revision handling
- Conflict detection (409 errors)

**Bulk Operations** ✅
- Bulk insert/update with individual result tracking

**Mango Queries** ✅
- MongoDB-style selectors (`$gt`, `$gte`, `$lt`, `$lte`, `$eq`, `$ne`, etc.)
- Field projection, pagination (limit/skip)

**CouchDB Views** ✅
- Query views with key/keys, startkey/endkey, limit/skip, descending
- Support for include_docs, group, reduce parameters
- ViewResult with convenience methods

## Usage Examples

### Basic Usage
```python
from couch import connect, CouchConfig

config = CouchConfig(url="http://localhost:5984", username="admin", password="password")

async with connect(config) as client:
    # Create database
    await client.create_database("users")
    db = client.database("users")

    # Save document
    result = await db.save({"name": "Alice", "age": 25})
    doc_id = result.id

    # Get document
    doc = await db.get(doc_id)

    # Update document
    doc["age"] = 26
    await db.save(doc)

    # Delete document
    await db.delete(doc_id, doc["_rev"])
```

### Mango Queries
```python
# Find with selector
results = await db.find(
    selector={"age": {"$gte": 18}},
    fields=["name", "age"],
    limit=10
)
for doc in results:
    print(doc["name"])
```

### CouchDB Views
```python
# Create design document
design_doc = {
    "_id": "_design/users",
    "views": {
        "by_age": {
            "map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"
        }
    }
}
await db.save(design_doc)

# Query view
results = await db.view("users", "by_age", startkey=18, endkey=65)
ages = results.keys()        # [25, 30, 35, ...]
names = results.values()     # ["Alice", "Charlie", "Bob", ...]

# With include_docs
results = await db.view("users", "by_age", include_docs=True)
for doc in results.docs():
    print(doc["email"])

# Multiple specific keys
results = await db.view("users", "by_age", keys=[25, 35])
```

### Bulk Operations
```python
docs = [
    {"_id": "user1", "name": "Alice", "age": 25},
    {"_id": "user2", "name": "Bob", "age": 35}
]
results = await db.bulk_save(docs)
for result in results:
    if result.ok:
        print(f"Success: {result.id}")
    else:
        print(f"Error: {result.error} - {result.reason}")
```

## Development Notes

### Testing
- **40 tests** across 6 files (test_couch, test_database, test_documents, test_bulk_operations, test_mango_queries, test_views)
- Shared fixtures in `tests/conftest.py`:
  - `client` - CouchClient with auto-cleanup
  - `db` - test_db Database instance
- All tests use TDD approach
- Pytest configured for automatic async mode

### Code Style
- Ruff with `select = ['ALL']` and specific ignores in `pyproject.toml`
- Full type hints throughout
- Pydantic validation for all CouchDB responses

### CouchDB API Endpoints
- `GET /` - Server info
- `PUT /{db}` - Create database
- `DELETE /{db}` - Delete database
- `GET /{db}` - Database info
- `POST /{db}` - Create doc (auto-generate _id)
- `PUT /{db}/{id}` - Create/update doc with _id
- `GET /{db}/{id}` - Get doc
- `DELETE /{db}/{id}?rev={rev}` - Delete doc
- `GET /{db}/_all_docs` - List all docs
- `POST /{db}/_bulk_docs` - Bulk operations
- `POST /{db}/_find` - Mango queries
- `GET/POST /{db}/_design/{ddoc}/_view/{view}` - Query views

### Design Principles
- Explicit async methods only (no dictionary syntax)
- Database-scoped operations through Database class
- Server-scoped operations through CouchClient
- Centralized error handling (DRY)
- Type safety with Pydantic models
