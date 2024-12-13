from typing import Optional, Dict, Any, Union
from datetime import datetime

from sqlmodel import Field as SQLModelField, JSON, Relationship, DateTime, Column, func, text
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.dialects.postgresql import TIMESTAMP

from ..categories.district_list import FileDistrictList
from ...abcs.validation_model_abc import RecordListABC
from ...funcs.record_keygen import RecordKeyGenerator
from ..model_bases import SQLModelBase
from ...utils.validation_helpers.district_codes import (
    CityDistrictCodes,
    CountyDistrictCodes,
    StateDistrictCodes,
    FederalDistrictCodes,
    StateCourtCodes,
    DistrictCourtCodes,
    CountyCourtCodes,
    MuncipalCourtCodes,
    SpecialCourtCodes,
)

DistrictCodesDB = SA_Enum(
    CityDistrictCodes,
    CountyDistrictCodes,
    StateDistrictCodes,
    FederalDistrictCodes,
    StateCourtCodes,
    DistrictCourtCodes,
    CountyCourtCodes,
    MuncipalCourtCodes,
    SpecialCourtCodes,
    name='district_codes',
    native_enum=False
)


# class DistrictSetLink(SQLModelBase, table=True):
#     district_set_id: Optional[str] = SQLModelField(default=None, foreign_key='filedistrictlist.id', primary_key=True)
#     district_id: Optional[str] = SQLModelField(default=None, foreign_key="district.id", primary_key=True)


# class DistrictSet(SQLModelBase, table=True):
#     id: str | None = SQLModelField(default=None, primary_key=True)
#     districts: list["District"] = Relationship(back_populates="district_set", link_model=DistrictSetLink)
#     records: list["RecordBaseModel"] = Relationship(back_populates="district_set")


# class DistrictLink(SQLModelBase, table=True):
#     district_set_id: Optional[str] = SQLModelField(default=None, foreign_key='districtset.id', primary_key=True)
#     district_id: Optional[str] = SQLModelField(default=None, foreign_key="district.id", primary_key=True)
#     record_id: Optional[int] = SQLModelField(default=None, foreign_key="recordbasemodel.id", primary_key=True)
#
#     district: "District" = Relationship(back_populates="district_links")
#     district_set: "DistrictSet" = Relationship(back_populates="district_links")
#     record: "RecordBaseModel" = Relationship(back_populates="district_link_records")


class District(RecordListABC, SQLModelBase, table=True):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    state_abbv: Optional[str] = SQLModelField(default=None, description="State abbreviation")
    city: Optional[str] = SQLModelField(default=None, description="City name")
    county: Optional[str] = SQLModelField(default=None, description="County name")
    type: Optional[str]= SQLModelField(
        default=None,
        sa_column=DistrictCodesDB,
        description="Type of district (e.g., 'city', 'county', 'court', 'state', 'federal')"
        )
    name: Optional[str] = SQLModelField(default=None, description="Name of the district")
    number: Optional[str] = SQLModelField(default=None, description="Number or ID of the district")
    attributes: Optional[Dict[str, Any]] = SQLModelField(
        default_factory=dict,
        description="Additional attributes specific to the district type",
        sa_type=JSON
    )
    district_set_id: Optional[str] = SQLModelField(default=None, foreign_key='filedistrictlist.id')
    created_at: datetime = SQLModelField(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    updated_at: datetime = SQLModelField(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=text("CURRENT_TIMESTAMP"),
        ),
        default=None
    )
    district_set: list["FileDistrictList"] = Relationship(back_populates="districts")

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.generate_hash_key()

    def generate_hash_key(self) -> str:
        _make_key = RecordKeyGenerator.generate_static_key
        if self.city:
            _id = _make_key((self.state_abbv, self.city, self.type, self.name, self.number))
        elif self.county:
            _id = _make_key((self.state_abbv, self.county, self.type, self.name, self.number))
        else:
            _id = _make_key((self.state_abbv, self.type, self.name, self.number))
        return _id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, District):
            return self.id == other.id
        return False

    def update(self, other: 'District'):
        if other.city and not self.city:
            self.city = other.city
        if other.county and not self.county:
            self.county = other.county
        if other.name and not self.name:
            self.name = other.name
        if other.number and not self.number:
            self.number = other.number
        if other.attributes:
            self.attributes.update(other.attributes)
