from typing import Optional

from sqlmodel import Field as SQLModelField, Relationship as SQLModelRelationship

from ...abcs.validation_model_abc import FileCategoryListABC
from ...funcs.record_keygen import RecordKeyGenerator




# class DistrictSetLink(SQLModel, table=True, link_model=True):
#     district_set_id: Optional[str] = SQLModelField(
#         default=None,
#         foreign_key='filedistrictlist.id',
#         primary_key=True)
#     district_id: Optional[str] = SQLModelField(
#         default=None,
#         foreign_key="district.id",
#         primary_key=True)


class FileDistrictList(FileCategoryListABC, table=True):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    districts: list["District"] = SQLModelRelationship(back_populates="district_set")
    record_set: list["RecordBaseModel"] = SQLModelRelationship(back_populates="district_set")

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.generate_hash_key()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def merge(self, other: "FileDistrictList"):
        for district in other.districts:
            self.add_or_update(district)
        self.id = self.generate_hash_key()
        return self

    def add_or_update(self, new_district: "District"):
        for existing_district in self.districts:
            if existing_district.id == new_district.id:
                existing_district.update(new_district)
                return
        self.districts.append(new_district)
        self.id = self.generate_hash_key()
        return self

    def generate_hash_key(self) -> str:
        return RecordKeyGenerator.generate_static_key(
            "_".join(
                sorted(
                    [str(district.id) for district in self.districts]
                )
            )
        )