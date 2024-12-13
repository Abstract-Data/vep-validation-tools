from typing import Dict, Any, List, Union
from pydantic_core import PydanticCustomError
from pydantic import AliasChoices, BaseModel
import re

from ..funcs.address_validation import AddressTypeList


def check_if_fields_exist(self):
    _person_details = self.person_details
    if not _person_details:
        raise PydanticCustomError(
            'missing_person_details',
            'Missing person details. Unable to generate a strong key to match with',
            {
                'validator_model': self.__class__.__name__,
                'method_type': 'model_validator',
                'method_name': 'set_validator_types'
            }
        )

    if not self.name and getattr_with_prefix('person_name', self.data):
        raise PydanticCustomError(
            'missing_name_object',
            'There is name data in the renamer, but unable to create a name object',
            {
                'validator_model': self.__class__.__name__,
                'method_type': 'model_validator',
                'method_name': 'set_validator_types'
            }
        )
    if not self.phone and (_phone_data := getattr_with_prefix('contact_phone', self.data)):
        if not len(_phone_data) == 1:
            raise PydanticCustomError(
                'missing_phone_object',
                'There is phone data in the renamer, but unable to create a phone object',
                {
                    'validator_model': self.__class__.__name__,
                    'method_type': 'model_validator',
                    'method_name': 'set_validator_types'
                }
            )
    if not any([x.address_type for x in self.address_list if x.address_type in AddressTypeList]):
        raise PydanticCustomError(
            'missing_address',
            'Missing address information. Unable to generate VEP keys',
            {
                'validator_model': self.__class__.__name__,
                'method_type': 'model_validator',
                'method_name': 'set_validator_types'
            }
        )
    elif self.data.settings.get('FILE-TYPE') == 'VOTERFILE':
        if not self.residential_address:
            raise PydanticCustomError(
                'missing_residential_address',
                'Missing residential address information for voter record.',
                {
                    'validator_model': self.__class__.__name__,
                    'method_type': 'model_validator',
                    'method_name': 'set_validator_types'
                }
            )

    if not self.voter_registration and getattr_with_prefix('voter', self.data):
        raise PydanticCustomError(
            'missing_voter_registration',
            'There is voter registration data in the renamer, but unable to create a voter registration object',
            {
                'validator_model': self.__class__.__name__,
                'method_type': 'model_validator',
                'method_name': 'set_validator_types'
            }
        )

    if not self.district_set.districts and getattr_with_prefix('district', self.data):
        raise PydanticCustomError(
            'missing_districts',
            'There is district data in the renamer, but unable to create a district object',
            {
                'validator_model': self.__class__.__name__,
                'method_type': 'model_validator',
                'method_name': 'set_validator_types'
            }
        )

    if not self.vendor_names and getattr_with_prefix('vendor_names', self.data):
        raise PydanticCustomError(
            'missing_vendors',
            'There is vendor data in the renamer, but unable to create a vendor object',
            {
                'validator_model': self.__class__.__name__,
                'method_type': 'model_validator',
                'method_name': 'set_validator_types'
            }
        )
    return self

def safe_dict_merge(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely merge any number of dictionaries, handling None values.

    Args:
        *dicts: Variable number of dictionaries to merge.

    Returns:
        A new dictionary containing all key-value pairs from the input dictionaries.
    """
    result = {}
    for d in dicts:
        if d is not None:
            result |= d  # This is equivalent to result.update(d) in Python 3.9+
    return result


def only_text_and_numbers(input_string):
    # Regex pattern to match non-numbers, non-letters, and non-spaces
    pattern = r'[^a-zA-Z0-9 ]'
    # Substitute the matched patterns with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string


def next_with_key_suffix(k: str, dict_: Dict[str, Any]) -> bool:
    return next((value for key, value in dict_.items() if key.endswith(k) and value), None)


def key_list_with_suffix(sfx: str, dict_: Dict[str, Any]) -> List[str]:
    return [key for key in dict_.keys() if key.endswith(sfx)]


def value_list_with_prefix(dict_: Dict[str, Any], *args: Union[str, List[str], tuple]) -> List[str]:
    # Flatten the args if they are lists or tuples
    prefixes = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            prefixes.extend(arg)
        else:
            prefixes.append(arg)

    return [value for key, value in dict_.items() if any(key.startswith(prefix) for prefix in prefixes) and value]


def dict_with_prefix(pfx: str, dict_: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in dict_.items() if key.startswith(pfx) and value}


def getattr_with_prefix(pfx: str, obj: Any) -> Dict[str, Any]:
    return {key: getattr(obj, key) for key in dir(obj) if key.startswith(pfx) and getattr(obj, key)}


def remove_empty_from_dict(dict_: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in dict_.items() if value}


def remove_prefix(d: Dict[str, Any], prefixes: List[str]) -> Dict[str, Any]:
    if not any(d):
        raise PydanticCustomError(
            'remove_prefix_func',
            'Dictionary is empty',
            None
        )
    return {k.replace(pfx, ''): v for k, v in d.items() if v for pfx in prefixes}


def if_null_none(*args):
    if isinstance(args, str):
        if args not in ["", "null"]:
            return AliasChoices(args)
    if isinstance(args, list):
        _fields = [field for field in args if field not in ["", "null"]]
        return AliasChoices(*_fields)
    return None


def check_for_state_in_addresses(self: BaseModel):
    _data = self.model_dump(exclude_none=True)
    if not (_state := self.settings.get('STATE')):
        raise ValueError("State must be provided in the settings.")

    _abbreviation = _state['abbreviation']
    def _search(t: str) -> dict | None:
        return {k: v for k, v in _data.items() if k.startswith(t)}

    def _has_state(d: dict):
        if d and not any(key.endswith('state') for key in d.keys()):
            _type = next(d.__iter__()).split('_')[0]
            if all(key for key in d.keys() if 'part' in key):
                return (f"{_type}_part_state", _abbreviation)
            else:
                return (f"{_type}_state", _abbreviation)
        return

    for _type in [_search('residence'), _search('mail')]:
        if _state := _has_state(_type):
            setattr(self, *_state)
    return self

