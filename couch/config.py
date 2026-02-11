from pydantic import SecretStr
from pydantic_settings import BaseSettings


class CouchConfig(BaseSettings):
    url: str
    username: str
    password: SecretStr
