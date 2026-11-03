from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, model_validator


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    source_url: str | None = Field(default=None, max_length=2048)
    source_token: str | None = Field(default=None, max_length=4096)


class ImportedRecord(BaseModel):
    external_id: str = Field(min_length=1, max_length=160)
    kind: Literal[
        "person",
        "case",
        "encounter",
        "event",
        "object",
        "prescription",
        "allergy",
        "administration",
    ]
    title: str = Field(min_length=1, max_length=200)
    version: int = Field(ge=1)
    status: Literal["draft", "active", "deleted"] = "draft"
    authorized: bool = False
    occurred_at: AwareDatetime
    data: dict = Field(default_factory=dict)
    related_ids: list[str] = Field(default_factory=list, max_length=100)
    simulated: bool = False

    @model_validator(mode="after")
    def validate_active(self):
        if self.status == "active" and not self.authorized:
            raise ValueError("Active records require explicit authorization")
        if self.status == "active" and self.kind in {"prescription", "allergy", "administration"}:
            if not self.related_ids:
                raise ValueError("Clinical records require a related person")
        return self


class ImportBatch(BaseModel):
    request_key: str = Field(min_length=1, max_length=128)
    records: list[ImportedRecord] = Field(min_length=1, max_length=100)


class NoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    occurred_at: AwareDatetime


class MedicationCheck(BaseModel):
    prescription_id: str
    observed_ingredient: str = Field(min_length=1, max_length=160)
    observed_concentration: str = Field(min_length=1, max_length=80)
    patient_confirmed: bool = False
    checked_at: datetime
