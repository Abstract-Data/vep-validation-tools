from __future__ import annotations
import abc
from typing import Optional, Annotated, Dict, Any, List, Tuple, Iterable, Type, Generator
import uuid
from datetime import datetime
import itertools
from collections import Counter
from dataclasses import dataclass, field

import pandas as pd
from pydantic import ValidationError, BaseModel, Field as PydanticField
from sqlmodel import SQLModel


InputRecords = Iterable[Dict[str, Any]] | Generator[Dict[str, Any], None, None] | Dict[str, Any]
PassedRecords = Iterable[SQLModel] | Generator[SQLModel, None, None]
InvalidRecords = Iterable[Dict[str, Any]] | Generator[Dict[str, Any], None, None]
ValidationResults = Tuple[PassedRecords, InvalidRecords]

ValidatorOutput = Tuple[str, SQLModel | Dict[str, Any]]
RunValidationOutput = Generator[ValidatorOutput, None, None]


class RecordErrorValidator(BaseModel):
    error_id: uuid.uuid4 = PydanticField(default_factory=uuid.uuid4)
    error_type: str
    data: dict
    created_at: Optional[datetime] = None


class ErrorDetails(BaseModel):
    point_of_failure: Annotated[str, ...]
    model: Annotated[str, ...]
    errors: Annotated[List[dict], PydanticField(default_factory=list)]


@dataclass
class CreateValidatorABC(abc.ABC):
    state_name: Tuple[str, str]
    validator: SQLModel
    errors: Optional[pd.DataFrame] = field(default=None)
    _records: Optional[InputRecords] = field(default=None, init=False)
    _validation_generator: Optional[RunValidationOutput] = field(default=None, init=False)
    _valid_count: int = field(default=0, init=False)
    _invalid_count: int = field(default=0, init=False)

    def __repr__(self):
        return f"Validation Model: {self.validator.__name__}"

    def validate_single_record(self, record: InputRecords) -> RunValidationOutput:
        try:
            validated = self.validator.model_validate(record)
            yield 'valid', validated
        except ValidationError as e:
            error_detail = ErrorDetails(
                model=self.validator.__name__,
                point_of_failure=self.validator.__name__,
                errors=e.errors()
                )
            yield 'invalid', error_detail

    def run_validation(self, records: InputRecords) -> None:
        self._records = records
        self._validation_generator = self._create_validation_generator()

    def _create_validation_generator(self) -> RunValidationOutput:
        if self._records is None:
            raise ValueError("run_validation must be called before creating the validation generator")

        for record in self._records:
            status, result = self.validate_single_record(record)
            if status == 'valid':
                self._valid_count += 1
            else:
                self._invalid_count += 1
            yield status, result

    @property
    def valid(self) -> PassedRecords:
        if self._validation_generator is None:
            raise ValueError("run_validation must be called before accessing valid records")
        valid_gen, self._validation_generator = itertools.tee(self._validation_generator)
        return (result for status, result in valid_gen if status == 'valid')

    @property
    def invalid(self) -> InvalidRecords:
        if self._validation_generator is None:
            raise ValueError("run_validation must be called before accessing invalid records")
        invalid_gen, self._validation_generator = itertools.tee(self._validation_generator)
        return (result for status, result in invalid_gen if status == 'invalid')

    @property
    def valid_count(self) -> int:
        return self._valid_count

    @property
    def invalid_count(self) -> int:
        return self._invalid_count

    def get_errors(self) -> pd.DataFrame:
        errors = list(self.invalid)
        self.errors = pd.DataFrame.from_dict(
            Counter(error['error_type'] for error in errors),
            orient="index",
            columns=["count"],
        )
        return self.errors
