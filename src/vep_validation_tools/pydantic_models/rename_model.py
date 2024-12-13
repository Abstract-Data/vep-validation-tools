import abc
from pathlib import Path
from typing import Optional, Dict, Annotated, Type, Any, List, Union

from pydantic import (
    Field,
    model_validator,
    AliasChoices,
    create_model,
)

from ..utils import renamer_funcs as rename_func
from ..utils.readers import TomlReader
from .config import ValidatorConfig
from ..abcs.toml_record_fields_abc import TomlFileFieldsABC


class RecordRenamer(ValidatorConfig, abc.ABC):
    """
    A Pydantic model for renaming records with various date fields and settings.

    Attributes:
        person_dob (Optional[str]): The date of birth of the person.
        person_dob_yearmonth (Optional[str]): The year and month of the person's date of birth.
        person_dob_year (Optional[str]): The year of the person's date of birth.
        person_dob_month (Optional[str]): The month of the person's date of birth.
        person_dob_day (Optional[str]): The day of the person's date of birth.
        voter_registration_date (Optional[str]): The date of voter registration.
        raw_data (Dict[str, Any]): A dictionary to store raw original data before transformation.
        date_format (Union[str, List[str]]): The date format(s) to be used.
        settings (Dict[str, Any]): Additional settings for the model.
    """
    person_dob: Annotated[Optional[str], Field(default=None)]
    person_dob_yearmonth: Annotated[Optional[str], Field(default=None)]
    person_dob_year: Annotated[Optional[str], Field(default=None)]
    person_dob_month: Annotated[Optional[str], Field(default=None)]
    person_dob_day: Annotated[Optional[str], Field(default=None)]
    voter_registration_date: Annotated[Optional[str], Field(default=None)]
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    date_format: Union[str, List[str]] = Field(...)
    settings: Dict[str, Any] = Field(default_factory=dict)
    pass


class VALIDATOR_FIELDS(TomlFileFieldsABC):
    """
    A class to read and store field mappings from a TOML file.

    Attributes:
        _state (str): The state for which the fields are being read.
        _field_path (Path): The path to the TOML file containing the field mappings.
    """

    @property
    def fields(self) -> Dict[str, str]:
        """
        Reads the field mappings from the TOML file.

        Returns:
            Dict[str, str]: A dictionary containing the field mappings.
        """
        _field_toml = TomlReader(file=self._field_path, name=self._state.lower()).data
        self._fields = _field_toml
        return self._fields


def create_renamed_model(state: str, field_path: Path) -> Type[ValidatorConfig]:
    """
    Creates a dynamic Pydantic model for renaming records based on the provided state and field path.

    Args:
        state (str): The state for which the model is being created.
        field_path (Path): The path to the TOML file containing the field mappings.

    Returns:
        Type[ValidatorConfig]: The dynamically created Pydantic model.
    """
    _fields = VALIDATOR_FIELDS(_state=state, _field_path=field_path)
    _not_null_fields = {k: k if v == "null" else v for k, v in _fields.FIELDS.items()}

    # _not_null_fields = {k: v for k, v in _fields.FIELDS.items() if v == "null"}  # Set fields that are not empty/null.
    _validators: Dict[str, Any] = {
        'clear_blank_strings': model_validator(mode='before')(rename_func.clear_blank_strings),
        'create_raw_data_dict': model_validator(mode='before')(rename_func.create_raw_data_dict),
        'check_for_address_state': model_validator(mode='after')(rename_func.check_address_has_state),
    }  # Validators for the renaming model.

    # Create the field name dictionary for the model.
    _field_name_dict = {}
    for k, v in _not_null_fields.items():
        if isinstance(v, list):
            _field_name_dict[k] = (
                Annotated[
                    Optional[str],
                    Field(
                        default=None,
                        validation_alias=AliasChoices(*v)
                    )
                ]
            )
        else:
            _field_name_dict[k] = (
                Annotated[
                    Optional[str],
                    Field(
                        default=None,
                        validation_alias=AliasChoices(v)
                    )
                ]
            )

    # Add the date format field to the model.
    _field_name_dict['date_format'] = (Union[str, List[str]], Field(default=_fields.FIELD_FORMATTING['date']))
    _field_name_dict['settings'] = (dict, Field(default=_fields.SETTINGS))

    # Add a field to store raw original data before transformation
    _field_name_dict['raw_data'] = (Dict[str, Any], Field(default_factory=dict))

    return create_model(
        'RecordRenamer',
        **_field_name_dict,
        __base__=RecordRenamer,
        __validators__=_validators
    )  # Create the model.
