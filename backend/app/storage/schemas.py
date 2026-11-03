import uuid
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator


class ConnectionInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    provider: Literal["r2", "s3"] = "r2"
    endpoint: str = Field(max_length=2048)
    bucket: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
    region: str = Field(default="auto", pattern=r"^[a-zA-Z0-9-]{1,80}$")
    prefix: str = Field(default="", max_length=1024)
    access_key: SecretStr | None = None
    secret_key: SecretStr | None = None

    @model_validator(mode="after")
    def paired(self):
        if bool(self.access_key) != bool(self.secret_key):
            raise ValueError("Provide both access key and secret key")
        if self.prefix:
            self.prefix = self.prefix.rstrip("/") + "/"
        return self


class ImportInput(BaseModel):
    request_key: str = Field(min_length=1, max_length=128)
    keys: list[str] = Field(min_length=1, max_length=100)
    audience: Literal["home", "work"] = "home"
    workspace_id: uuid.UUID | None = None


class SyncInput(BaseModel):
    prefix: str = Field(default="", max_length=1024)
    audience: Literal["home", "work"] = "home"
    workspace_id: uuid.UUID | None = None
    interval_minutes: Literal[15, 60, 1440] = 60
    enabled: bool = False


class KeyInput(BaseModel):
    key: str = Field(min_length=1, max_length=1024)
