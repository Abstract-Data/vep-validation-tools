import datetime
from typing import Dict, Any
from enum import StrEnum
import asyncio

from sqlmodel import Field as SQLModelField, JSON, Relationship, SQLModel, Session, select, Relationship, ForeignKey
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.future import select as async_select
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from pydantic import model_validator
from pydantic.alias_generators import to_snake

from election_utils.election_models import ElectionTypeDetails, ElectionVote, ElectionVoteMethod, ElectionTurnoutCalculator

from .fields.person_name import PersonName, PersonNameLink
from .fields.voter_registration import VoterRegistration
from .fields.address import Address, AddressLink
from .fields.phone_number import ValidatedPhoneNumber, PhoneLink
from .fields.vendor import VendorTags, VendorName, VendorTagsToVendorLink, VendorTagsToVendorToRecordLink
from .fields.vep_keys import VEPMatch
from .fields.data_source import DataSource
from .fields.input_data import InputData
from .fields.district import District, FileDistrictList

# from ..db_models.categories.district_list import FileDistrictList


# TODO: Consider storing the PreValidationCleanup as a PrivateAttr on the model so it can be referenced
#  to create the relationship model. This will allow for the model to be created dynamically.

# TODO: Make sure there are not SETS in the Validated RecordBaseModel or else it will throw an error.
#  Sets must be a list.

# TODO: Attempt to put back relationships in each model respectively, using forward refs where appropriate.
#  Use 'ForwardRefs' for RecordBaseModel.

MODEL_LIST = [Address, PersonName, VoterRegistration, ValidatedPhoneNumber, VendorName, VendorTags, ElectionTypeDetails,
              ElectionVoteMethod, ElectionVote, DataSource, InputData, VEPMatch, District, ]

def lower_snake(s: str) -> str:
    return to_snake(s).lower()

sn = lower_snake

class RecordBaseModel(SQLModel, table=True):
    id: int | None = SQLModelField(
        default=None,
        primary_key=True)
    name_id: str | None = SQLModelField(
        default=None,
        foreign_key=f'{PersonName.__tablename__}.id')
    voter_registration_id: str | None = SQLModelField(
        default=None,
        foreign_key=f'{VoterRegistration.__tablename__}.vuid',
        unique=True)
    district_set_id: str | None = SQLModelField(default=None, foreign_key="filedistrictlist.id")
    vep_keys_id: int | None = SQLModelField(
        default=None,
        foreign_key=f'{VEPMatch.__tablename__}.id')
    input_data_id: int | None = SQLModelField(
        default=None,
        foreign_key=f'{InputData.__tablename__}.id')
    data_source_id: str | None = SQLModelField(
        default=None,
        foreign_key=f'datasource.file')
    name: "PersonName" = Relationship(
        back_populates='records', link_model=PersonNameLink)
    voter_registration: "VoterRegistration" = Relationship(
        back_populates='records')
    address_list: list["Address"] = Relationship(
        back_populates='records',
        link_model=AddressLink)
    district_set: "FileDistrictList" = Relationship(back_populates="record_set")
    phone_numbers: list["ValidatedPhoneNumber"] = Relationship(
        back_populates='records',
        link_model=PhoneLink)
    vendor_tag_record_links: list["VendorTagsToVendorToRecordLink"] = Relationship(
        back_populates='record')
    vote_history: list["ElectionVote"] = Relationship(
        back_populates="record"
    )
    election_scores: "ElectionTurnoutCalculator" = SQLModelField(default=None, sa_type=JSON)
    vep_keys: "VEPMatch" = Relationship(
        back_populates='records')
    input_data: "InputData" = Relationship(
        back_populates='records')
    data_source: "DataSource" = Relationship(
        back_populates='records',)
        # link_model=DataSourceLink)

    @staticmethod
    def add_created_and_updated_columns():
        for model in MODEL_LIST:
            model.add_created_and_update_columns()

    @staticmethod
    def _query_one_or_none(stmt: select, session: Session):
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def set_relationships(data: "PreValidationCleanUp", engine: Engine):
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            query_one_or_none_ = RecordBaseModel._query_one_or_none
            _name = select(PersonName).where(PersonName.id == data.name.id)
            _voter_registration = select(VoterRegistration).where(VoterRegistration.vuid == data.voter_registration.vuid)
            _input_data = select(InputData).where(InputData.id == data.input_data.id)
    
            if not (existing_name := query_one_or_none_(_name, session)):
                session.add(data.name)
            else:
                data.name = existing_name
    
            if not (existing_voter_registration := query_one_or_none_(_voter_registration, session)):
                session.add(data.voter_registration)
            else:
                data.voter_registration = existing_voter_registration
    
            if data.vep_keys:
                _vep_keys = select(VEPMatch).where(VEPMatch.id == data.vep_keys.id)
                if not (existing_vep_keys := query_one_or_none_(_vep_keys, session)):
                    session.add(data.vep_keys)
                else:
                    data.vep_keys = existing_vep_keys
    
            if not (existing_input_data := query_one_or_none_(_input_data, session)):
                session.add(data.input_data)
            else:
                data.input_data = existing_input_data
            session.flush()
    
            _final = RecordBaseModel(
                name=data.name,
                voter_registration_id=data.voter_registration.id,
                voter_registration=data.voter_registration,
                vep_keys=data.vep_keys,
                input_data=data.input_data
            )
            session.add(_final)
    
            for address in data.address_list:
                _check_address = select(Address).where(Address.id == address.id)
                if not (existing_address := query_one_or_none_(_check_address, session)):
                    session.add(address)
                else:
                    address = existing_address
                _final.address_list.append(address)
    
            if data.data_source:
                for data_source in data.data_source:
                    _check_data_source = select(DataSource).where(DataSource.file == data_source.file)
                    if not (existing_data_source := query_one_or_none_(_check_data_source, session)):
                        session.add(data_source)
                    else:
                        data_source = existing_data_source
                        session.merge(data_source)
                    _final.data_source.append(data_source)
            session.commit()
    
            # Merge elections
            if data.elections:
                for election in data.elections:
                    _check_election = select(ElectionTypeDetails).where(ElectionTypeDetails.id == election.election.id)
                    _check_vote_method = select(ElectionVoteMethod).where(ElectionVoteMethod.id == election.vote_method.id)
                    if not (existing_election := query_one_or_none_(_check_election, session)):
                        session.add(election.election)
                    else:
                        election.election = existing_election
    
                    if not (existing_vote_method := query_one_or_none_(_check_vote_method, session)):
                        session.add(election.vote_method)
                    else:
                        election.vote_method = existing_vote_method
                    _final.vote_history.append(election.vote_record)
    
            if data.district_set:
                data.district_set.id = data.district_set.generate_hash_key()
                _check_district_set = select(FileDistrictList).where(FileDistrictList.id == data.district_set.id)
                existing_district_set = query_one_or_none_(_check_district_set, session)
                if existing_district_set:
                    # Merge the existing district set with the new one
                    for district in data.district_set.districts:
                        if district not in existing_district_set.districts:
                            existing_district_set.districts.add_or_update(district)
                    session.merge(existing_district_set)
                else:
                    # Add the new district set
                    session.add(data.district_set)
                _final.district_set_id = data.district_set.id
    
            if data.vendor_names:
                _check_vendor_names = select(VendorName).where(VendorName.id == data.vendor_names.id)
                if not (existing_vendor_names := query_one_or_none_(_check_vendor_names, session)):
                    session.add(data.vendor_names)
                else:
                    data.vendor_names = existing_vendor_names
    
                if data.vendor_tags:
                    _check_vendor_tags = select(VendorTags).where(VendorTags.id == data.vendor_tags.id)
                    if not (existing_vendor_tags := query_one_or_none_(_check_vendor_tags, session)):
                        session.add(data.vendor_tags)
                    else:
                        data.vendor_tags = existing_vendor_tags
                    data.vendor_names.tags.append(data.vendor_tags)
                    _final.vendor_tag_record_links.append(data.vendor_tags)
            session.commit()


    def flatten(self):
        data = {
            'first_name': self.name.first,
            'last_name': self.name.last,
            'voter_id': self.voter_registration.vuid,
            'dob': self.name.dob,
        }

        for address in self.address_list:
            data[sn(f"{address.address_type}_std")] = address.standardized
            data[sn(f"{address.address_type}_city")] = address.city
            data[sn(f"{address.address_type}_state")] = address.state
            data[sn(f"{address.address_type}_zip")] = address.zip5

        if self.district_set:
            for district in self.district_set.districts:
                data[sn(f"{district.type}_{district.name}")] = district.number

        if self.phone_numbers:
            for phone in self.phone_numbers:
                data[sn(f"{phone.phone_type}_phone")] = phone.phone

        if self.vote_history:
            for election in self.vote_history:
                data[sn(f"{election.year}{election.election_type}_method")] = next(
                    (x.vote_method for x in self.vote_history if x.election == election), None)
                if election.party:
                    data[sn(f"{election.year}{election.election_type}_party")] = next(
                        (x.party for x in self.vote_history if x.election == election), None)

        return data

    # @staticmethod
    # async def async_set_relationships(data: "PreValidationCleanUp", engine: AsyncEngine):
    #
    #     async with AsyncSession(engine) as session:
    #         async with session.begin():
    #             async def query_one_or_none_(stmt):
    #                 result = await session.execute(stmt)
    #                 return result.scalar_one_or_none()
    #
    #             _name = async_select(PersonName).where(PersonName.id == data.name.id)
    #             _voter_registration = async_select(VoterRegistration).where(VoterRegistration.vuid == data.voter_registration.vuid)
    #             _vep_keys = async_select(VEPMatch).where(VEPMatch.id == data.vep_keys.id)
    #             _input_data = async_select(InputData).where(InputData.id == data.input_data.id)
    #             _data_source = async_select(DataSource).where(DataSource.file == data.data_source.file)
    #
    #             if not (existing_name := await query_one_or_none_(_name)):
    #                 session.add(data.name)
    #             else:
    #                 data.name = existing_name
    #
    #             if not (existing_voter_registration := await query_one_or_none_(_voter_registration)):
    #                 session.add(data.voter_registration)
    #             else:
    #                 data.voter_registration = existing_voter_registration
    #
    #             if not (existing_vep_keys := await query_one_or_none_(_vep_keys)):
    #                 session.add(data.vep_keys)
    #             else:
    #                 data.vep_keys = existing_vep_keys
    #
    #             if not (existing_input_data := await query_one_or_none_(_input_data)):
    #                 session.add(data.input_data)
    #             else:
    #                 data.input_data = existing_input_data
    #
    #             await session.flush()
    #
    #             _final = RecordBaseModel(
    #                 name=data.name,
    #                 voter_registration_id=data.voter_registration.id,
    #                 voter_registration=data.voter_registration,
    #                 vep_keys=data.vep_keys,
    #                 input_data=data.input_data
    #             )
    #             session.add(_final)
    #             await session.flush()
    #
    #             async def process_address(address):
    #                 _check_address = async_select(Address).where(Address.id == address.id)
    #                 if not (existing_address := await query_one_or_none_(_check_address)):
    #                     session.add(address)
    #                 else:
    #                     if address.is_mailing:
    #                         address.is_mailing = existing_address.is_mailing
    #                     if address.is_residence:
    #                         address.is_residence = existing_address.is_residence
    #                     address = existing_address
    #                 _final.address_list.append(address)
    #
    #             await asyncio.gather(*[process_address(address) for address in data.address_list])
    #
    #             if data.data_source:
    #                 _check_data_source = async_select(DataSource).where(DataSource.file == data.data_source.file)
    #                 if not (existing_data_source := await query_one_or_none_(_check_data_source)):
    #                     session.add(data.data_source)
    #                 else:
    #                     data.data_source = existing_data_source
    #                 _final.data_source.append(data.data_source)
    #
    #             if data.elections:
    #                 async def process_election(election):
    #                     _check_election = async_select(ElectionTypeDetails).where(ElectionTypeDetails.id == election.election.id)
    #                     _check_vote_method = async_select(ElectionVoteMethod).where(ElectionVoteMethod.id == election.vote_method.id)
    #                     if not (existing_election := await query_one_or_none_(_check_election)):
    #                         session.add(election.election)
    #                     else:
    #                         election.election = existing_election
    #
    #                     if not (existing_vote_method := await query_one_or_none_(_check_vote_method)):
    #                         session.add(election.vote_method)
    #                     else:
    #                         election.vote_method = existing_vote_method
    #                     _final.vote_history.append(election.vote_record)
    #
    #                 await asyncio.gather(*[process_election(election) for election in data.elections])
    #
    #             if data.district_set:
    #                 _check_district_set = async_select(FileDistrictList).where(FileDistrictList.id == data.district_set.id)
    #                 existing_district_set = await query_one_or_none_(_check_district_set)
    #                 if existing_district_set:
    #                     existing_district_set.merge(data.district_set)
    #                     data.district_set = existing_district_set
    #                 else:
    #                     session.add(data.district_set)
    #                 _final.district_set_id = data.district_set.id
    #
    #             if data.vendor_names:
    #                 _check_vendor_names = async_select(VendorName).where(VendorName.id == data.vendor_names.id)
    #                 if not (existing_vendor_names := await query_one_or_none_(_check_vendor_names)):
    #                     session.add(data.vendor_names)
    #                 else:
    #                     data.vendor_names = existing_vendor_names
    #
    #                 if data.vendor_tags:
    #                     _check_vendor_tags = async_select(VendorTags).where(VendorTags.id == data.vendor_tags.id)
    #                     if not (existing_vendor_tags := await query_one_or_none_(_check_vendor_tags)):
    #                         session.add(data.vendor_tags)
    #                     else:
    #                         data.vendor_tags = existing_vendor_tags
    #                     data.vendor_names.tags.append(data.vendor_tags)
    #                     _final.vendor_tag_record_links.append(data.vendor_tags)

    # def create_flat_record(self):
    #     data = {
    #         'first_name': self.name.first,
    #         'last_name': self.name.last,
    #         'voter_id': self.voter_registration.vuid,
    #         'dob': self.name.dob,
    #     }
    #
    #     for address in self.address_list:
    #         data[f"{address.address_type}_std"] = address.standardized
    #         data[f"{address.address_type}_city"] = address.city
    #         data[f"{address.address_type}_state"] = address.state
    #         data[f"{address.address_type}_zip"] = address.zip5
    #
    #     if self.districts:
    #         for district in self.districts:
    #             data[f"{district.type}_{district.name}".replace(" ", "_")] = district.county
    #
    #     if self.phone:
    #         for phone in self.phone:
    #             data[f"{phone.phone_type}_PHONE"] = phone.phone
    #
    #     if self.elections:
    #         for election in self.elections:
    #             data[f"{election.year}{election.election_type}_METHOD"] = next(
    #                 (x.vote_method for x in self.vote_history if x.election == election), None)
    #             data[f"{election.year}{election.election_type}_PARTY"] = next(
    #                 (x.party for x in self.vote_history if x.election == election), None)
    #
    #     return data

# class RecordBaseModel(_model_bases.ValidatorBaseModel, table=True):
#     name: PersonName | None = SQLModelField(default=None)
#     voter_registration: VoterRegistration | None = SQLModelField(default=None)
#     # mailing_id: Annotated[Optional[str], PydanticField(default=None)]
#     # residential_id: Annotated[Optional[str], PydanticField(default=None)]
#     address_list: set['Address'] = SQLModelField(default_factory=set)
#     district_set: FileDistrictList | None = SQLModelField(default=None, description='List of district records')
#     phone: list["ValidatedPhoneNumber"] | None = SQLModelField(default_factory=list)
#     vendor_names: set[VendorName] | None = SQLModelField(default_factory=set)
#     vendor_tags: list["VendorTags"] | None = SQLModelField(default_factory=list)
#     elections: list["ElectionTypeDetails"] | None = SQLModelField(default_factory=list,
#                                                                   description='List of election history records')
#     vote_history: list["VotedInElection"] | None = SQLModelField(default_factory=list)
#     unassigned: Dict[str, Any] | None = SQLModelField(default=None)
#     vep_keys: VEPMatch = SQLModelField(default_factory=VEPMatch)
#     # corrected_errors: Annotated[Dict[str, Any], PydanticField(default_factory=dict)]
#     input_data: InputData = SQLModelField(default_factory=InputData)
#     data_source: DataSource = SQLModelField(default_factory=DataSource)
#     db_model: SQLModel | None = None
#
#     def __init__(self, **data):
#         super().__init__(**data)
#         RecordBaseModel.__tablename__ = self.input_data.settings.get('FILE-TYPE')
#
#
#     def create_flat_record(self):
#         data = {
#             'first_name': self.name.first,
#             'last_name': self.name.last,
#             'voter_id': self.voter_registration.vuid,
#             'dob': self.name.dob,
#         }
#
#         for address in self.address_list:
#             data[f"{address.address_type}_std"] = address.standardized
#             data[f"{address.address_type}_city"] = address.city
#             data[f"{address.address_type}_state"] = address.state
#             data[f"{address.address_type}_zip"] = address.zip5
#
#         if self.districts:
#             for district in self.districts:
#                 data[f"{district.type}_{district.name}".replace(" ", "_")] = district.county
#
#         if self.phone:
#             for phone in self.phone:
#                 data[f"{phone.phone_type}_PHONE"] = phone.phone
#
#         if self.elections:
#             for election in self.elections:
#                 data[f"{election.year}{election.election_type}_METHOD"] = next(
#                     (x.vote_method for x in self.vote_history if x.election == election), None)
#                 data[f"{election.year}{election.election_type}_PARTY"] = next(
#                     (x.party for x in self.vote_history if x.election == election), None)
#
#         return data
# session.merge(tables.voter_registration(**self.voter_registration.model_dump()))
# session.merge(self.input_data)
# if session.exec(select(DataSource).where(DataSource.file == self.data_source.file)).first():
#     session.merge(self.data_source)
# else:
#     session.add(self.data_source)
#     session.commit()
#     session.refresh(self.data_source)
#
# _model = self.db_model(
#     name_id=self.name.id,
#     voter_registration_id=self.voter_registration.id,
#     vep_keys_id=self.vep_keys.id,
#     input_data_id=self.input_data.id
# )
# session.add(_model)
#
# session.add(DataSourceLink(data_source_id=self.data_source.id, record_id=_model.id))
# session.add(_model)
# session.commit()
# session.refresh(_model)
#
#
# for address in self.address_list:
#     session.merge(address)
#     session.add(
#         RecordAddressLink(
#             address_id=address.id,
#             record_id=_model.id,
#             is_mailing=address.is_mailing,
#             is_residence=address.is_residence
#         )
#     )
#
# if self.district_set:
#     for district in self.district_set.districts:
#         session.add(district)
#         session.add(RecordDistrictLink(district_id=district.id, record_id=_model.id))
#
# if self.phone:
#     for phone in self.phone:
#         session.add(phone)
#         session.add(RecordPhoneLink(phone_id=phone.id, record_id=_model.id))
#
# if self.vote_history:
#     session.add_all([x for x in self.elections])
#     for vote in self.vote_history:
#         session.add(vote)
#         session.add(
#             RecordElectionLink(
#                 election_id=vote.election_id,
#                 vote_details_id=vote.id,
#                 record_id=_model.id
#             )
#         )
#
# if self.vendor_names:
#     for vendor in self.vendor_names:
#         session.add(vendor)
#         session.refresh(vendor)
#
# if self.vendor_tags:
#     for tag in self.vendor_tags:
#         session.add(tag)
#         session.add(VendorNameToTagLink(vendor_id=vendor.id, tag_id=tag.id))
#         session.add(RecordVendorTagLink(tag_id=tag.id, record_id=_model.id))
# session.commit()
# return _model

# class RecordModel(Base):
#     __abstract__ = True
#
#     @declared_attr
#     @abc.abstractmethod
#     def name_id(cls) -> Mapped[Optional[int]]:
#         return mapped_column(Integer, ForeignKey(f'{cls.__name__}_person_name.id'), nullable=True)
#
#     @declared_attr
#     @abc.abstractmethod
#     def voter_registration_id(cls) -> Mapped[Optional[int]]:
#         return mapped_column(Integer, ForeignKey(f'{cls.__name__}_voter_registration.id'), nullable=True)
#
#     @declared_attr
#     @abc.abstractmethod
#     def data_source_id(cls) -> Mapped[int]:
#         return mapped_column(Integer, ForeignKey(f'{cls.__name__}_data_source.id'), nullable=False)
#
#     # @abstract_declared_attr
#     # def address_list_id(cls):
#     #     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_address.id'), nullable=True)
#     #
#     # @abstract_declared_attr
#     # def phones_id(cls) -> Mapped[Optional[int]]:
#     #     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_validated_phone_number.id'), nullable=True)
#     # @declared_attr
#     # def residential_address_id(cls) -> Mapped[Optional[int]]:
#     #     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_residential_address.id'), nullable=True)
#     #
#     # @declared_attr
#     # def mailing_address_id(cls) -> Mapped[Optional[int]]:
#     #     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_mailing_address.id'), nullable=True)
#
#     # @declared_attr
#     # def districts_id(cls) -> Mapped[Optional[int]]:
#     #     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_government_districts.id'), nullable=True)
#
#     # @declared_attr
#     # def vendors_id(cls) -> Mapped[Optional[int]]:
#     #     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_vendor_tags.id'), nullable=True)
#
#     @declared_attr
#     @abc.abstractmethod
#     def vep_keys_id(cls) -> Mapped[Optional[int]]:
#         return mapped_column(Integer, ForeignKey(f'{cls.__name__}_vep_keys.id'), nullable=True)
#
#     @declared_attr
#     @abc.abstractmethod
#     def input_data_id(cls) -> Mapped[Optional[int]]:
#         return mapped_column(Integer, ForeignKey(f'{cls.__name__}_input_data.id'), nullable=True)
#
#     @declared_attr
#     @abc.abstractmethod
#     def name(cls) -> Mapped[Optional['PersonNameModel']]:
#         return relationship(f'{cls.__name__}PersonNameModel', back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def voter_registration(cls) -> Mapped[Optional['VoterRegistrationModel']]:
#         return relationship(f'{cls.__name__}VoterRegistrationModel', back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def address_list(cls) -> Mapped[Optional[List['AddressModel']]]:
#         return relationship(f'{cls.__name__}AddressModel', back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def districts(cls) -> Mapped[Optional['IndividualDistrictModel']]:
#         return relationship(
#             f'{cls.__name__}IndividualDistrictsModel',
#             back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def phone_numbers(cls) -> Mapped[List['ValidatedPhoneNumberModel']]:
#         return relationship(f'{cls.__name__}ValidatedPhoneNumberModel')
#
#     @declared_attr
#     @abc.abstractmethod
#     def vendor_tags(cls) -> Mapped[Optional['VendorTagsModel']]:
#         return relationship(f'{cls.__name__}VendorTagsModel', back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def vep_keys(cls) -> Mapped[Optional['VEPKeysModel']]:
#         return relationship(f'{cls.__name__}VEPKeysModel', back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def input_data(cls) -> Mapped[Optional['InputDataModel']]:
#         return relationship(f'{cls.__name__}InputDataModel', back_populates='record')
#
#     @declared_attr
#     @abc.abstractmethod
#     def data_sources(cls) -> Mapped[List['DataSourceModel']]:
#         return relationship(f'{cls.__name__}DataSourceModel', back_populates='record')
#
#     @classmethod
#     def create_dynamic_model(cls, table_name: str, schema_name: str = None):
#         class DynamicRecord(cls):
#             __tablename__ = table_name
#             __table_args__ = {'schema': schema_name} if schema_name else {}
#
#             if table_name.lower().startswith('voterfile'):
#                 @declared_attr
#                 def election_history(cls) -> Mapped[List['ElectionHistoryModel']]:
#                     return relationship(
#                         f'{cls.__name__}ElectionHistory',
#                         back_populates='record',
#                         cascade="all, delete-orphan"
#                     )
#
#                 @declared_attr
#                 def election_history_id(cls) -> Mapped[Optional[int]]:
#                     return mapped_column(Integer, ForeignKey(f'{cls.__name__}_election_history.id'), nullable=True)
#
#
# class RelatedModels(abc.ABC):
#     RECORD: 'RecordModel'
#     RECORD_VIEW: 'RecordView'
#     NAME: 'PersonNameModel'
#     VOTER_REGISTRATION: 'VoterRegistrationModel'
#     ADDRESS: 'AddressModel'
#     INDIVIDUAL_DISTRICT: 'DistrictModel'
#     RECORD_DISTRICT: 'RecordDistrictModel'
#     PHONE_NUMBER: 'ValidatedPhoneNumberModel'
#     VEP_KEYS: 'VEPKeysModel'
#     VENDOR_TAGS: 'VendorTagsModel'
#     INPUT_DATA: 'InputDataModel'
#     INDIVIDUAL_ELECTION: 'ElectionTypeModel'
