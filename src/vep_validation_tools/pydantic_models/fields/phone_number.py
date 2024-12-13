from typing import Optional, Dict, Any, ForwardRef

from pydantic_extra_types.phone_numbers import PhoneNumber as PydanticPhoneNumber

from sqlmodel import Field as SQLModelField, JSON, Relationship

from ...abcs.validation_model_abc import RecordListABC
from ...funcs.record_keygen import RecordKeyGenerator
from ..model_bases import SQLModelBase


class PhoneLink(SQLModelBase, table=True):
    __tablename__ = 'phone_link'
    phone_id: Optional[str] = SQLModelField(
        default=None,
        foreign_key="validatedphonenumber.id",
        primary_key=True)
    record_id: Optional[int] = SQLModelField(
        default=None,
        foreign_key=f'recordbasemodel.id',
        primary_key=True)


class ValidatedPhoneNumber(RecordListABC, SQLModelBase, table=True):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    phone_type: str | None = SQLModelField(default=None)
    phone: PydanticPhoneNumber = SQLModelField()
    areacode: str | None = SQLModelField(default=None)
    number: str | None = SQLModelField(default=None)
    reliability: str | None = SQLModelField(default=None)
    other_fields: Dict[str, Any] | None = SQLModelField(sa_type=JSON, default_factory=dict)
    records: list["RecordBaseModel"] = Relationship(back_populates='phone_numbers', link_model=PhoneLink)

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.generate_hash_key()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def generate_hash_key(self) -> str:
        return RecordKeyGenerator.generate_static_key(self.phone)

    def update(self, other: "ValidatedPhoneNumber"):
        self.phone = other.phone
        self.areacode = other.areacode
        self.number = other.number
        self.reliability = other.reliability
        self.other_fields = other.other_fields