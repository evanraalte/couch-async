from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    reason: str


class CouchError(Exception):
    def __init__(self, response: ErrorResponse) -> None:
        self.response = response
        super().__init__(f"{response.error}: {response.reason}")


class DatabaseAlreadyExistsError(CouchError):
    pass


class DatabaseNotFoundError(CouchError):
    pass


class DocumentNotFoundError(CouchError):
    pass


class DocumentConflictError(CouchError):
    pass
