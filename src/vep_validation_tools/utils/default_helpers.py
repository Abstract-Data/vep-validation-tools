from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, NamedTuple, Annotated, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field, model_validator
from collections import OrderedDict
import usaddress


""" === TYPE HINTS === """
AddressValidatorField = str
FileFieldName = str


""" 
========== CONSTANTS ==========
"""

OLDEST_PERSON_IN_THE_WORLD = datetime(1907, 3, 4)

PHONE_FIELD_TYPES = ['mobile', 'landline', 'unknown']
PHONE_NUMBER_FIELD_PREFIX = 'contact_'

ADDRESS_FIELD_NAMES: Tuple[AddressValidatorField, FileFieldName] = ('residential', 'residence'), ('mailing', 'mail')


CONTACT_PHONE_PREFIX = 'contact_phone'

VEP_KEY_FIELD_ENDSWITH = ['first', 'last', 'dob', 'zip5']

ADDRESS1_PREFIXES = ["number", "number_prefix", "street_pre_directional", "street_pre_type",
                     "street_pre_modifier",
                     "street_name", "street_type", "street_post_directional", "street_post_modifier",
                     "street_post_type"]

ADDRESS2_PREFIXES = ["unit_type", "unit_num"]

""" === PATH CREATION FUNCTIONS === """


# TODO: Determine if this func is even needed (7/6/2024)
def generate_voterfile_field_folder_path(state: str) -> Path:
    return Path(__file__).parents[2] / "data" / "fields" / "voterfiles" / state.lower() / "statewide.toml"


"""
========== CLASSES ==========
"""
class USAddressFields(NamedTuple):
    component_value: str
    component_name: str


class AddressLinesDict(OrderedDict):
    address1: str
    address2: str
    city: str
    state: str
    zip5: str
    zip4: str
    standardized: str


class AddressLinesOrdered(BaseModel):
    address1: Annotated[Optional[str], Field(default=None)]
    address2: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    state: Annotated[Optional[str], Field(default=None)]
    zip5: Annotated[Optional[str], Field(default=None)]
    zip4: Annotated[Optional[str], Field(default=None)]
    zipcode: Annotated[Optional[str], Field(default=None)]
    standardized: Annotated[Optional[str], Field(default=None)]


    # @model_validator(mode='after')
    # def create_zipcode(self):
    #     while True:
    #         if self.zip5:
    #             if len(self.zip5) == 5:
    #                 if self.zip4 and len(self.zip4) == 4:
    #                     self.zipcode = f"{self.zip5}-{self.zip4}"
    #                 else:
    #                     self.zipcode = self.zip5
    #                 break
    #             else:
    #                 # Handle the case where zip5 is not of length 5 (if needed)
    #                 self.zip5 = None
    #                 break
    #         else:
    #             # Handle the case where zip5 is not present (if needed)
    #             break
    #     return self
    #
    # @model_validator(mode='after')
    # def standardize_address(self):
    #     std = " ".join([x for x in [self.address1, self.address2] if x])
    #     if all([std, self.city, self.state, self.zipcode]):
    #         std += f", {self.city}, {self.state} {self.zipcode}"
    #         self.standardized = std
    #     return self


class AddressPartsDict(BaseModel):
    AddressNumberPrefix: Annotated[Optional[List[str] | str], Field(default=None)]
    AddressNumber: Annotated[Optional[List[str] | str], Field(default=None)]
    AddressNumberSuffix: Annotated[Optional[List[str] | str], Field(default=None)]
    StreetNamePreModifier: Annotated[Optional[List[str] | str], Field(default=None)]
    StreetNamePreDirectional: Annotated[Optional[List[str] | str], Field(default=None)]
    StreetNamePreType: Annotated[Optional[List[str] | str], Field(default=None)]
    StreetName: Annotated[Optional[List[str] | str], Field(default=None)]
    StreetNamePostType: Annotated[Optional[List[str] | str], Field(default=None)]
    StreetNamePostDirectional: Annotated[Optional[List[str] | str], Field(default=None)]
    BuildingName: Annotated[Optional[List[str] | str], Field(default=None)]
    OccupancyType: Annotated[Optional[List[str] | str], Field(default=None)]
    OccupancyIdentifier: Annotated[Optional[List[str] | str], Field(default=None)]
    PlaceName: Annotated[Optional[List[str] | str], Field(default=None)]
    StateName: Annotated[Optional[List[str] | str], Field(default=None)]
    ZipCode: Annotated[Optional[List[str] | str], Field(default=None)]
    ZipPlus4: Annotated[Optional[List[str] | str], Field(default=None)]
    USPSBoxType: Annotated[Optional[List[str] | str], Field(default=None)]
    USPSBoxID: Annotated[Optional[List[str] | str], Field(default=None)]
    USPSBoxGroupType: Annotated[Optional[List[str] | str], Field(default=None)]
    USPSBoxGroupID: Annotated[Optional[List[str] | str], Field(default=None)]


@dataclass
class FIELD_NAME_AND_ALIASES(NamedTuple):
    PERSON_NAME = [
        ('prefix', 'name_prefix'),
        ('first', 'name_first'),
        ('last', 'name_last'),
        ('middle', 'name_middle'),
        ('suffix', 'name_suffix'),
        ('dob', 'dob'),
        ('gender', 'gender'),
        ('county', 'voter_county')
    ]

    VOTER_REGISTRATION = [
        ('vuid', 'vuid'),
        ('edr', 'registration_date'),
        ('status', 'registration_status'),
        ('political_party', 'political_party'),
        ('precinct_name', 'precinct_name'),
        ('precinct_number', 'precinct_number')
    ]
    COURT_DISTRICTS = [
        ('county', 'court_county'),
        ('municipal', 'court_municipal'),
        ('appellate', 'court_appellate'),
    ]
    CITY_DISTRICTS = [
        ('name', 'city_name'),
        ('school_district', 'city_school_district'),
    ]

    COUNTY_DISTRICTS = [
        ('number', 'county_number'),
        ('id', 'county_id'),
        ('township', 'county_township'),
        ('village', 'county_village'),
        ('ward', 'county_ward'),
        ('local_school_district', 'county_local_school_district'),
        ('library', 'county_library'),
        ('career_center', 'county_career_center'),
        ('education_service_center', 'county_education_service_center'),
        ('excempted_village_school_district', 'county_exempted_village_school_district'),
    ]

    STATE_DISTRICTS = [
        ('board_of_education', 'state_board_of_education'),
        ('legislative_upper', 'state_legislative_upper'),
        ('legislative_lower', 'state_legislative_lower')
    ]

    FEDERAL_DISTRICTS = [
        ('congressional', 'federal_congressional'),
    ]


@dataclass
class ADDRESS_PARSER_FIELDS:
    ADDRESS1 = dict.fromkeys([
        'AddressNumberPrefix',
        'AddressNumber',
        'AddressNumberSuffix',
        'StreetNamePreModifier',
        'StreetNamePreDirectional',
        'StreetNamePreType',
        'StreetName',
        'StreetNamePostType',
        'StreetNamePostDirectional', ])
    ADDRESS2 = dict.fromkeys([
        'BuildingName',
        'OccupancyType',
        'OccupancyIdentifier',
    ])

    CITY = dict.fromkeys([
        'PlaceName',
    ])

    STATE = dict.fromkeys([
        'StateName',
    ])
    ZIPCODE = dict.fromkeys([
        'ZipCode',
        'ZipPlus4',
        'SubaddressType',
        'SubaddressIdentifier',
    ])
    USPS = dict.fromkeys([
        'USPSBoxType',
        'USPSBoxID',
        'USPSBoxGroupType',
        'USPSBoxGroupID',
    ])



