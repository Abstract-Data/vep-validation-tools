from typing import Dict, Any

from sqlmodel import Field as SQLModelField, JSON, Relationship
from ..model_bases import SQLModelBase


class InputData(SQLModelBase, table=True):
    __tablename__ = 'input_data'
    id: int | None = SQLModelField(default=None, primary_key=True)
    input_data: Dict[str, Any] | None = SQLModelField(sa_type=JSON, default=None)
    original_data: Dict[str, Any] | None = SQLModelField(sa_type=JSON, default=None)
    renamed_data: Dict[str, Any] | None = SQLModelField(sa_type=JSON, default=None)
    corrections: Dict[str, Any] | None = SQLModelField(sa_type=JSON, default=None)
    settings: Dict[str, Any] | None = SQLModelField(sa_type=JSON, default=None)
    date_format: Dict[str, Any] | str | None = SQLModelField(sa_type=JSON, default=None)
    records: 'RecordBaseModel' = Relationship(back_populates='input_data')
    