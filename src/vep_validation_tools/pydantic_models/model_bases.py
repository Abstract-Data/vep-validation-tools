import abc
from sqlmodel import SQLModel
from pydantic import ConfigDict

from .config import ValidatorConfig


class ValidatorBaseModel(ValidatorConfig):
    pass


class SQLModelBase(SQLModel, abc.ABC):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )
