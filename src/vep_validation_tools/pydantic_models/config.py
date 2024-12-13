from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
# from logfire.integrations.pydantic import PluginSettings

from sqlmodel import SQLModel


class ValidatorConfig(SQLModel):
    """
    A class that defines the configuration for a validator.

    Attributes:
        model_config (ConfigDict): A dictionary that holds the configuration settings for the model.

            The settings include:
                - from_attributes (bool): If True, populates the dictionary from the model's attributes.
                - populate_by_name (bool): If True, populates the dictionary by the model's name.
                - str_to_upper (bool): If True, converts string values to uppercase.
                - str_strip_whitespace (bool): If True, strips whitespace from string values.
                - validate_default (bool): If True, validates the default values.
                - arbitrary_types_allowed (bool): If True, allows arbitrary types.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
        # alias_generator=AliasGenerator(
        #     serialization_alias=lambda field_name: to_camel(field_name)
        # )
    )


# TODO: Check and see if the 'name' is not a valid string issue is happening because of the alias generator.
