from __future__ import annotations
import abc
from typing import Optional, Annotated
from dataclasses import dataclass

from sqlmodel import Field as SQLModelField, SQLModel


class ValidationListBaseABC(SQLModel, abc.ABC):
    pass


class FileCategoryListABC(ValidationListBaseABC):
    id: Annotated[Optional[str], SQLModelField(default=None)]

    @abc.abstractmethod
    def add_or_update(self, new_record: SQLModel):
        pass

    @abc.abstractmethod
    def generate_hash_key(self) -> str:
        pass


class RecordListABC(ValidationListBaseABC):
    id: Annotated[str, SQLModelField(default_factory=lambda: '')]

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.generate_hash_key()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, RecordListABC):
            return self.id == other.id
        return False

    @abc.abstractmethod
    def generate_hash_key(self) -> str | RecordListABC:
        pass

    @abc.abstractmethod
    def update(self, other: SQLModel):
        pass

