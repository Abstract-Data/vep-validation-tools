from typing import Dict, Any
from pydantic import BaseModel
from pydantic_core import PydanticCustomError


def create_raw_data_dict(cls, values) -> Dict[str, Any]:
    _raw_values = values.copy()
    values['raw_data'] = _raw_values
    return values


def clear_blank_strings(cls, values) -> Dict[str, Any]:
    """
    Clear out all blank strings or ones that contain 'null' from records.
    :param cls:
    :param values:
    :return:
    """
    for k, v in values.items():
        if v in ["", '"', "null"]:
            values[k] = None
        if k in ["", '"', "null"]:
            values[k] = values[k].replace(k, None)
    return values


def check_address_has_state(self: BaseModel):
    if not (_state := self.settings.get('STATE')):
        raise ValueError("State must be provided in the settings.")
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

    _data = self.model_dump(exclude_none=True)
    _abbreviation = _state['abbreviation']
    for _type in [_search('residence'), _search('mail')]:
        if _state := _has_state(_type):
            setattr(self, *_state)
    return self