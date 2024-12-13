from typing import Dict, Any, Optional

from sqlmodel import Field as SQLModelField

from .config import ValidatorConfig
from .rename_model import RecordRenamer
from .fields.person_name import PersonName
from .fields.voter_registration import VoterRegistration
from .fields.address import Address, AddressLink
from .fields.phone_number import ValidatedPhoneNumber, PhoneLink
from .fields.vendor import VendorTags, VendorName, VendorTagsToVendorLink, VendorTagsToVendorToRecordLink
from .fields.vep_keys import VEPMatch
from .fields.data_source import DataSource
from .fields.input_data import InputData
from .categories.district_list import FileDistrictList
from election_utils.election_models import ElectionDataTuple, ElectionTurnoutCalculator


class CleanUpBaseModel(ValidatorConfig):
    data: RecordRenamer = SQLModelField(...)
    name: Optional[PersonName] = SQLModelField(default=None)
    voter_registration: Optional[VoterRegistration] = SQLModelField(default=None)
    person_details: Dict[str, Any] = SQLModelField(default_factory=dict)
    input_voter_registration: Dict[str, Any] = SQLModelField(default_factory=dict)
    district_set: FileDistrictList = SQLModelField(default_factory=FileDistrictList)

    phone: list[ValidatedPhoneNumber] = SQLModelField(default_factory=list)
    address_list: list['Address'] = SQLModelField(default_factory=list)
    date_format: Any = SQLModelField(default=None)
    settings: Dict[str, Any] = SQLModelField(default=None)
    raw_data: Dict[str, Any] = SQLModelField(default=None)
    vendor_names: list[VendorName] = SQLModelField(default_factory=list)
    vendor_tags: list[VendorTags] = SQLModelField(default_factory=list)
    vendor_record: list[VendorTagsToVendorToRecordLink] = SQLModelField(default_factory=list)
    elections: list[ElectionDataTuple] = SQLModelField(default_factory=list)
    election_scores: Optional[ElectionTurnoutCalculator] = SQLModelField(default=None)
    corrected_errors: dict[str, Any] = SQLModelField(default_factory=dict)
    data_source: list[DataSource] = SQLModelField(default_factory=list)
    input_data: Optional[InputData] = SQLModelField(default=None)
    vep_keys: Optional[VEPMatch] = SQLModelField(default=None)
