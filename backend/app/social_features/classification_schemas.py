"""Inputs shared by publication services and HTTP routes."""

import uuid

from pydantic import BaseModel, Field, field_validator


class ClassificationInput(BaseModel):
    category_id: uuid.UUID
    tag_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


class TermInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = " ".join(value.split())
        if not value:
            raise ValueError("A name is required.")
        return value


class TermUpdate(TermInput):
    active: bool = True
