from __future__ import annotations
from typing import Dict, List, Tuple, Optional

import phonenumbers

from pydantic.dataclasses import dataclass as pydantic_dataclass

from ..utils import default_helpers as helpers
from ..utils import default_funcs as vfuncs
from ..pydantic_models.fields.phone_number import ValidatedPhoneNumber


@pydantic_dataclass
class PhoneNumberValidationFuncs:

    @staticmethod
    def check_if_valid_phone(phone_num: str) -> Tuple[phonenumbers.PhoneNumber | None, List[str]]:
        number_corrections = []
        _correct_number = None
        try:
            _correct_number = phonenumbers.parse(phone_num, "US")
        except phonenumbers.phonenumberutil.NumberParseException:
            number_corrections.append('Phone number is not a valid US phone number')
            _correct_number = None
        if _correct_number and not phonenumbers.is_valid_number(_correct_number):
            number_corrections.append('Phone number is not a valid US phone number')
            _correct_number = None
        if not _correct_number:
            number_corrections.append('Phone number is not a valid US phone number')
        return _correct_number, number_corrections

    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[Optional[phonenumbers.PhoneNumber], List[str]]:
        try:
            parsed_number = phonenumbers.parse(phone, "US")
            if phonenumbers.is_valid_number(parsed_number):
                return parsed_number, ["Phone number successfully validated"]
            else:
                return None, ["Phone number is not a valid US phone number"]
        except phonenumbers.NumberParseException:
            return None, ["Failed to parse phone number"]

    @staticmethod
    def format_phone_number(phone: phonenumbers.PhoneNumber) -> Dict[str, str]:
        formatted = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        national_number = str(phone.national_number)
        return {
            "phone": formatted,
            "areacode": national_number[:3],
            "number": national_number[3:]
        }

    @staticmethod
    def validate_phones(self):
        _func = PhoneNumberValidationFuncs
        phone_list = []
        all_corrections = {}
        input_phone_dict = vfuncs.getattr_with_prefix(helpers.CONTACT_PHONE_PREFIX, getattr(self, 'data', None))

        if not input_phone_dict:
            self.phone = None
            return self

        for key, value in input_phone_dict.items():
            if not key.startswith(helpers.CONTACT_PHONE_PREFIX) or not value:
                continue

            phone_type = key.split('_')[2]
            type_prefix = f'{helpers.CONTACT_PHONE_PREFIX}_{phone_type}'

            full_phone = input_phone_dict.get(type_prefix)
            phone_areacode = input_phone_dict.get(f'{type_prefix}_areacode')
            phone_number = input_phone_dict.get(f'{type_prefix}_number')

            corrections = []

            if full_phone:
                parsed_phone, parse_corrections = _func.validate_phone_number(full_phone)
                corrections.extend(parse_corrections)

                if parsed_phone:
                    phone_data = _func.format_phone_number(parsed_phone)
                    phone_data['phone_type'] = phone_type
                    phone_data['reliability'] = input_phone_dict.get(f'{type_prefix}_reliability')
                    phone_list.append(ValidatedPhoneNumber(**phone_data))
                    corrections.append(f'{phone_type} was successfully validated and formatted')

            if phone_areacode and phone_number:
                if len(phone_areacode) == 3 and len(phone_number) == 7:
                    merged_number = f"{phone_areacode}{phone_number}"
                    parsed_merged, merge_corrections = _func.validate_phone_number(merged_number)
                    corrections.extend(merge_corrections)

                    if parsed_merged:
                        formatted_merged = _func.format_phone_number(parsed_merged)
                        formatted_merged['phone_type'] = phone_type
                        formatted_merged['reliability'] = input_phone_dict.get(f'{type_prefix}_reliability')

                        if not any(p.phone == formatted_merged['phone'] for p in phone_list):
                            phone_list.append(ValidatedPhoneNumber(**formatted_merged))
                            corrections.append(f'Additional number added for {phone_type}')

            if corrections:
                all_corrections[phone_type] = corrections

        if phone_list:
            self.corrected_errors.update({f'phone_{k}': v for k, v in all_corrections.items()})
            self.phone = phone_list
        else:
            self.phone = None

        return self


# from __future__ import annotations
# import abc
# from typing import Optional, Annotated
# from dataclasses import dataclass

# from sqlmodel import Field as SQLModelField, SQLModel


# class ValidationListBaseABC(SQLModel, abc.ABC):
#     pass


# class FileCategoryListABC(ValidationListBaseABC):
#     id: Annotated[Optional[str], SQLModelField(default=None)]

#     @abc.abstractmethod
#     def add_or_update(self, new_record: SQLModel):
#         pass

#     @abc.abstractmethod
#     def generate_hash_key(self) -> str:
#         pass


# class RecordListABC(ValidationListBaseABC):
#     id: Annotated[str, SQLModelField(default_factory=lambda: '')]

#     def __init__(self, **data):
#         super().__init__(**data)
#         self.id = self.generate_hash_key()

#     def __hash__(self):
#         return hash(self.id)

#     def __eq__(self, other):
#         if isinstance(other, RecordListABC):
#             return self.id == other.id
#         return False

#     @abc.abstractmethod
#     def generate_hash_key(self) -> str | RecordListABC:
#         pass

#     @abc.abstractmethod
#     def update(self, other: SQLModel):
#         pass

