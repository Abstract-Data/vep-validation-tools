from typing import Any, Dict

from sqlmodel import Field as SQLModelField, JSON, SQLModel


class CustomFields(SQLModel, table=True):
    __tablename__ = 'custom_fields'
    fields: Dict[str, Any] | None = SQLModelField(default=None, sa_type=JSON)
    