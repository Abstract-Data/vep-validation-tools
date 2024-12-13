from dataclasses import dataclass
import abc
from ..utils.readers import TomlReader
from typing import Any, Dict
from pathlib import Path


@dataclass
class TomlFileFieldsABC(abc.ABC):
    _state: str
    _field_path: Path
    _fields: Dict[str, Any] = None

    def __post_init__(self):
        self.SETTINGS = self.fields.get('SETTINGS')
        self.FIELD_FORMATTING = self.fields.get('SETTINGS').get('FIELD-FORMATTING')
        self.VOTER_ID_LENGTHS = self.fields.get('SETTINGS').get('VOTER-ID')
        self.REPLACE_TEXT = self.fields.get('SETTINGS').get('REPLACE-CHARS')
        self.FIELDS = self.fields.get('FIELDS')

    @property
    @abc.abstractmethod
    def fields(self) -> Dict[str, Any]:
        _field_toml = TomlReader(file=self._field_path, name=self._state.lower()).data
        self._fields = _field_toml
        return self._fields
