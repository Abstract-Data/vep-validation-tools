from typing import Dict, Any, Optional

from sqlmodel import Field as SQLModelField, JSON, Relationship, SQLModel, ForeignKey

from ...abcs.validation_model_abc import RecordListABC
from ...funcs.record_keygen import RecordKeyGenerator
from ..model_bases import SQLModelBase


# class VendorNameToTagLink(SQLModel):
#     # __tablename__ = 'vendor_name_tags_link'
#     vendor_id: Optional[str] = SQLModelField(default=None, foreign_key='vendor_name.id', primary_key=True)
#     tag_id: Optional[int] = SQLModelField(default=None, foreign_key='vendor_tags.id', primary_key=True)
class VendorTagsToVendorLink(SQLModelBase, table=True, link_model=True):
    __tablename__ = 'vendor_tags_to_vendor_link'
    vendor_id: Optional[int] = SQLModelField(
        default=None,
        foreign_key=f"vendor_tags.id",
        primary_key=True,
        unique=True)
    tag_id: Optional[str] = SQLModelField(
        default=None,
        foreign_key=f"vendor_name.id",
        primary_key=True,
        unique=True)


class VendorTags(SQLModelBase, table=True):
    __tablename__ = 'vendor_tags'
    id: Optional[int] = SQLModelField(default=None, primary_key=True)
    tags: Dict[str, Any] = SQLModelField(
        ...,
        description="List of tags associated with the vendor",
        sa_type=JSON)
    vendors: list["VendorName"] = Relationship(
        back_populates="tags",
        link_model=VendorTagsToVendorLink)


class VendorName(RecordListABC, SQLModelBase, table=True):
    __tablename__ = 'vendor_name'
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    name: str = SQLModelField(...)
    tags: list["VendorTags"] = Relationship(back_populates="vendors", link_model=VendorTagsToVendorLink)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def generate_hash_key(self) -> str:
        return RecordKeyGenerator.generate_static_key(self.name)

    def update(self, new_record: 'VendorName'):
        self.name = new_record.name


class VendorTagsToVendorToRecordLink(SQLModelBase, table=True, link_model=True):
    __tablename__ = 'vendor_tags_to_vendor_to_record_link'
    vendor_tag_link_id: Optional[int] = SQLModelField(
        default=None,
        foreign_key=f"{VendorTagsToVendorLink.__tablename__}.vendor_id",
        primary_key=True)
    record_id: Optional[int] = SQLModelField(
        default=None,
        foreign_key="recordbasemodel.id",
        primary_key=True)
    record: "RecordBaseModel" = Relationship(back_populates='vendor_tag_record_links')