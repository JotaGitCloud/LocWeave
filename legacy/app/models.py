from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    strings: Mapped[list["StringEntry"]] = relationship(back_populates="project")

class StringEntry(Base):
    __tablename__ = "string_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    string_key: Mapped[str] = mapped_column(String(255))
    source_text: Mapped[str] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_length: Mapped[int | None] = mapped_column(nullable=True)

    project: Mapped["Project"] = relationship(back_populates="strings")
    translations: Mapped[list["Translation"]] = relationship(back_populates="string_entry")

class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True)
    string_entry_id: Mapped[int] = mapped_column(ForeignKey("string_entries.id"))
    language: Mapped[str] = mapped_column(String(10))
    translated_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    string_entry: Mapped["StringEntry"] = relationship(back_populates="translations")