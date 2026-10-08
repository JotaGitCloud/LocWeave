from pydantic import BaseModel
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class StringEntryCreate(BaseModel):
    string_key: str
    source_text: str
    context: str | None = None
    max_length: int | None = None

class StringEntryOut(BaseModel):
    id: int
    string_key: str
    source_text: str
    context: str | None
    max_length: int | None

    class Config:
        from_attributes = True