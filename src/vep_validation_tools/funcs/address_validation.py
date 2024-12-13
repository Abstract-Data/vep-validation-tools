
from typing import Any, Dict, List
from functools import partial
from enum import StrEnum

import usaddress
from rapidfuzz import fuzz
from scourgify import NormalizeAddress
from scourgify.exceptions import AddressNormalizationError

from pydantic import BaseModel
from pydantic_core import PydanticCustomError
from pydantic.dataclasses import dataclass as pydantic_dataclass

from ..utils import default_helpers as helpers
from ..utils import default_funcs as vfuncs
from .record_keygen import RecordKeyGenerator
from ..pydantic_models.rename_model import RecordRenamer


AddressCorrections = Dict[str, List[str]]

NEEDED_ADDRESS_PARTS = ['address1', 'address1', 'city', 'state', 'zip5', 'zip4']

OUTPUT_ADDRESS_DICT_KEYS = ['address_parts', 'zipcode', 'county', 'standardized', 'key'] + NEEDED_ADDRESS_PARTS


class AddressType(StrEnum):
    RESIDENCE = 'residence'
    MAIL = 'mail'


AddressTypeList = [AddressType.MAIL, AddressType.RESIDENCE]

AddressLinesAndPartsDict = dict[str, Dict[str, helpers.AddressPartsDict | helpers.AddressLinesOrdered]]

@pydantic_dataclass
class AddressValidationFuncs:

    @staticmethod
    def create_address_lines(address_dict: dict, _type: str) -> helpers.AddressLinesOrdered:
        if _type in AddressTypeList:
            d = address_dict
            _city, _state, _zip5, _adr_str = None, None, None, None
            if all([key.startswith(f"{_type}_part") for key in d]):
                for k, v in d.items():
                    if k.startswith(f"{_type}_part"):
                        match k.split('_')[-1]:
                            case 'city':
                                _city = v
                            case 'state':
                                _state = v
                            case 'zip5':
                                _zip5 = v
                        _adr_str = " ".join(
                            [
                                v for k, v in d.items()
                                if k.startswith(f"{_type}_part")
                                   and (
                                           v and v not in [
                                       y for y in [_city, _state, _zip5] if y
                                   ]
                                   )
                            ]
                        )
                        if _city:
                            _adr_str += f" {_city}"
                        if _state:
                            _adr_str += f" {_state}"
                        if _zip5:
                            _adr_str += f" {_zip5}"
            elif any(key.startswith(_type) for key in d):
                _adr_str = " ".join(
                    v for k, v in d.items()
                    if k.startswith(_type) and v
                )
                _adr_str = " ".join([v for k, v in d.items() if k.startswith(f"{_type}") and v])

            _new_address = {}
            try:
                _std = NormalizeAddress(_adr_str).normalize()
            except AddressNormalizationError as e:
                _std = None
                _reattempt_parse = usaddress.parse(_adr_str)
                for part, type_ in _reattempt_parse:
                    match type_:
                        case "USPSBoxType":
                            if _adr1 := _new_address.get('address1'):
                                _new_address['address1'] += f" {part}".strip()
                            else:
                                _new_address['address1'] = part
                        case "USPSBoxID":
                            if _new_address.get('address1'):
                                _new_address['address1'] += f" {part}".strip()
                            else:
                                _new_address['address1'] = part
                        case "PlaceName":
                            if _new_address.get('city'):
                                _new_address['city'] += f" {part}".strip()
                            else:
                                _new_address['city'] = part
                        case "StateName":
                            if _new_address.get('state'):
                                _new_address['state'] += f" {part}".strip()
                            else:
                                _new_address['state'] = part
                        case "ZipCode":
                            if _new_address.get('zip5'):
                                _new_address['zip5'] += f" {part}".strip()
                            else:
                                _new_address['zip5'] = part

            if _std:
                if (adr1 := _std.get('address_line_1', None)):
                    _new_address["address1"] = adr1
                if (adr2 := _std.get('address_line_2', None)):
                    _new_address["address2"] = adr2
                if city := _std.get('city', None):
                    _new_address["city"] = city
                if state := _std.get('state', None):
                    _new_address["state"] = state
                if _zip := _std.get('postal_code', None):
                    _split =_zip.split('-')
                    _new_address["zip5"] = _split[0]
                    if len(_split) > 1:
                        _new_address["zip4"] = _split[1]
            _new_address['standardized'] = ", ".join([v for k, v in _new_address.items() if v])
            return helpers.AddressLinesOrdered(**_new_address)

    @staticmethod
    def create_address_parts(
            address_lines: helpers.AddressLinesOrdered
    ) -> AddressLinesAndPartsDict:

        address_dict = {'lines': address_lines}
        _parsed = usaddress.parse(address_lines.standardized.replace(',', ""))
        # Join parsed parts keys if they have the same values
        _parts = {}
        for _part, _type in _parsed:
            if _type in _parts:
                _parts[_type] += f" {_part}"
            else:
                _parts[_type] = _part
        address_dict['parts'] = helpers.AddressPartsDict(**_parts)
        return address_dict
