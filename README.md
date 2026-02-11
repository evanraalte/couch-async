# couch-async

Async HTTP/2 client library for CouchDB 3.x with type-safe interfaces using httpx and Pydantic.

## Features

- Async HTTP/2 connections via httpx
- Type-safe responses with Pydantic models
- Document CRUD with revision handling and conflict detection
- Bulk operations
- Mango queries (MongoDB-style selectors)
- CouchDB views with convenience methods

## Installation

```bash
pip install couch-async
```

## Quick Start

```python
from couch import connect, CouchConfig

config = CouchConfig(url="http://localhost:5984", username="admin", password="password")

async with connect(config) as client:
    await client.create_database("mydb")
    db = client.database("mydb")

    # Save a document
    result = await db.save({"name": "Alice", "age": 25})

    # Get it back
    doc = await db.get(result.id)

    # Update
    doc["age"] = 26
    await db.save(doc)

    # Mango query
    results = await db.find(
        selector={"age": {"$gte": 18}},
        fields=["name", "age"],
        limit=10,
    )
    for doc in results:
        print(doc["name"])
```

## Views

```python
# Create a design document
await db.save({
    "_id": "_design/users",
    "views": {
        "by_age": {
            "map": "function(doc) { if (doc.age) emit(doc.age, doc.name); }"
        }
    }
})

# Query the view
results = await db.view("users", "by_age", startkey=18, endkey=65)
ages = results.keys()
names = results.values()
```

## Bulk Operations

```python
docs = [
    {"_id": "user1", "name": "Alice", "age": 25},
    {"_id": "user2", "name": "Bob", "age": 35},
]
results = await db.bulk_save(docs)
```

## Development

### Prerequisites

- Python 3.12+
- Docker

### Running CouchDB

The project includes a `compose.yml` that starts a single-node CouchDB 3.x instance:

```bash
docker compose up -d
```

CouchDB will be available at http://localhost:5984 (admin/password).

### Running Tests

```bash
uv run pytest -vvv
```

## License

MIT
