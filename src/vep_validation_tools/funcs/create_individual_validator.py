from __future__ import annotations
import multiprocessing
from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple, Any, Type, List, Annotated, Optional, Union, Generator, Set
from collections import Counter, defaultdict
import itertools
from datetime import datetime
import uuid
from functools import partial
from contextlib import ExitStack

import pandas as pd
from pydantic import ValidationError, BaseModel, Field as PydanticField
from rich.progress import Progress

from ..pydantic_models.cleanup_model import (
    PreValidationCleanUp,
    Address,
    District,
    ElectionTypeDetails,
    VendorName,
    VotedInElection,
    RecordRenamer,
    ValidatorConfig
)
from .pydantic_models.record import RecordBaseModel

# Define type aliases for readability
PassedRecords = Iterable[Type[ValidatorConfig]]
InvalidRecords = Iterable[Type[ValidatorConfig]]
ValidationResults = Tuple[PassedRecords, InvalidRecords]


def default_max_workers():
    return max(1, multiprocessing.cpu_count() - 1)


class RecordErrorValidator(BaseModel):
    error_id: uuid.uuid4 = PydanticField(default_factory=uuid.uuid4)
    error_type: str
    data: dict
    created_at: Optional[datetime] = None


class ErrorDetails(ValidatorConfig):
    point_of_failure: Annotated[str, ...]
    record_values: Annotated[Dict[str, Any], ...]
    rename_values: Annotated[RecordRenamer, PydanticField(default=None)]
    cleanup_values: Annotated[Optional[Dict[str, Any]], PydanticField(default=None)]
    models: Annotated[Dict[str, str], PydanticField(default={
        'rename': ValidatorConfig.__name__,
        'cleanup': PreValidationCleanUp.__name__,
        'final': RecordBaseModel.__name__
    })]
    errors: Annotated[List[dict], PydanticField(default_factory=list)]


@dataclass
class CreateValidator:
    """
    A class used to validate records using a specified validator.

    Attributes
    ----------
    renaming_validator: Type[BaseModel]
        The validator to be used for renaming records.
    record_validator : Type[BaseModel]
        The validator to be used for validating records.
    error_validator : Type[RecordErrorValidator]
        The validator to be used for validating error records.
    valid : PassedRecords
        The records that passed validation.
    invalid : InvalidRecords
        The records that failed validation.
    errors : pd.DataFrame
        A DataFrame containing the count of each error type.
    """
    state_name: Tuple[str, str]
    renaming_validator: Type[ValidatorConfig]
    record_validator: Type[RecordBaseModel]
    cleanup_validator: PreValidationCleanUp = field(default=PreValidationCleanUp)
    error_validator: RecordErrorValidator = field(default=RecordErrorValidator)
    valid: PassedRecords = field(default=None)
    invalid: InvalidRecords = field(default=None)
    errors: pd.DataFrame = field(default=None)
    elections: Set[ElectionTypeDetails] = field(default_factory=set)
    vote_types: Set[VotedInElection] = field(default_factory=set)
    districts: Set[District] = field(default_factory=set)
    addresses: Set[Address] = field(default_factory=set)
    vendors: Set[VendorName] = field(default_factory=set)
    _input_record_counter: int = 0
    _valid_counter: int = 0
    _invalid_counter: int = 0
    _iter_count: int = field(default=0)

    def __repr__(self):
        """Returns a string representation of the validator used."""
        return f"Validation Model: {self.record_validator.__name__}"

    @property
    def logger(self):
        """Returns a logger instance with the module name set to 'CreateValidator'."""
        # return Logger(module_name="CreateValidator")
        return None

    def validate_record(self, _record: Dict[str, Any]) -> Tuple[str, Union[Dict[str, Any], ErrorDetails]]:
        error_info = partial(
            ErrorDetails,
            record_values=_record,
            models={
                'rename': self.renaming_validator.__name__,
                'cleanup': self.cleanup_validator.__name__,
                'final': self.record_validator.__name__
            }
        )
        self._input_record_counter += 1

        def attempt_validation(
                _record_to_validate: BaseModel | Dict[str, Any],
                _validator: Type[BaseModel],
                _validation_stage: str,
                _error_func: Type[ErrorDetails] = error_info,
                **kwargs):
            if isinstance(_record_to_validate, BaseModel):
                record_dict = dict(_record_to_validate)
            elif isinstance(_record_to_validate, dict):
                record_dict = _record_to_validate
            else:
                raise ValueError("Record must be a BaseModel or a dict.")

            if kwargs.get('use_model_validate', True):
                _validator = partial(_validator.model_validate, record_dict)
            else:
                _validator = partial(_validator, **record_dict)

            try:
                sucessful_validation = _validator()
                return 'valid', sucessful_validation
            except ValidationError as e:
                record_dict["error_type"] = f"{e.errors()[0]['type']} : {e.errors()[0]['msg']}"
                _error = e
                return "invalid", _error_func(
                    point_of_failure=_validation_stage,
                    errors=_error.errors()
                )

        status, result = attempt_validation(
            _record_to_validate=_record,
            _validator=self.renaming_validator,
            _validation_stage="rename",
            _error_func=error_info
        )
        if status == "valid":
            # _renamed = dict(result)
            _renamed_dict = {
                'data': result
            }

            cleanup_error_info = partial(
                error_info,
                point_of_failure="cleanup",
                rename_values=result)
            status, result = attempt_validation(
                _record_to_validate=_renamed_dict,
                _validator=self.cleanup_validator,
                _validation_stage="cleanup",
                _error_func=cleanup_error_info,
                use_model_validate=False
            )

            if status == "valid":
                if hasattr(result, 'collected_districts'):
                    for district in result.collected_districts:
                        self.districts.add(district)
                if hasattr(result, 'collected_elections'):
                    for election in result.collected_elections:
                        self.elections.add(election)
                if hasattr(result, "collected_addresses"):
                    for address in result.collected_addresses:
                        self.addresses.add(address)
                if hasattr(result, "collected_vendors"):
                    for vendor in result.collected_vendors:
                        self.vendors.add(vendor)
                if hasattr(result, 'collected_votes'):
                    for vote in result.collected_votes:
                         self.vote_types.add(vote.election)

                # _cleanup = result.model_dump(
                #     exclude={
                #         'data',
                #         'collected_districts',
                #         'collected_elections',
                #         'collected_addresses',
                #         'collected_vendors',
                #         'collected_votes'
                #     }
                # )
                #
                # final_error_info = partial(
                #     error_info,
                #     point_of_failure="final",
                #     rename_values=_cleanup,
                #     cleanup_values=_cleanup,
                # )
                # status, result = attempt_validation(
                #     _record_to_validate=result,
                #     _validator=self.record_validator,
                #     _validation_stage="final",
                #     _error_func=final_error_info
                # )
                # return status, result
            return status, result
        return status, result

    def validation_generator(
            self,
            _records: Iterable[Dict[str, Any]] | List[Dict[str, Any]]
    ) -> ValidationResults:
        """
        A generator that validates each record and yields either a valid record or an invalid record.

        Parameters
        ----------
        _records : Generator[Dict[str, Any], None, None]
            The records to be validated.

        Yields
        ------
        ValidationResults
            A tuple containing generators of valid and invalid records.
        """

        for record in _records:
            yield self.validate_record(_record=record)

    def run_validation(self,
                       records: Iterable[Dict[str, Any]]) -> "CreateValidator":
        """
        Runs the validation on the records and sets the valid and invalid records.

        Parameters
        ----------
        records : Generator[Dict[str, Any], None, None] or List[Dict[str, Any]]
            The records to be validated.

        Returns
        -------
        CreateValidator
            The instance of the CreateValidator class.

        Args:
            renaming_validator:
        """
        # self.logger.info(f"Running validation...")
        _validation_gen = itertools.tee(self.validation_generator(
            _records=records), 2)

        _statuses = ["valid", "invalid"]

        def get_records(result_type: str):
            stats = {}
            if self._iter_count > 1:
                raise ValueError("No other validation iterators available.")
            if (result_type := result_type.lower()) not in _statuses:
                raise ValueError("result_type must be either 'valid' or 'invalid'")

            with ExitStack() as stack:
                ctx = logfire.span(
                    f"Getting {result_type} {self.state_name[1]} records for {self.state_name[0].title()}...")
                stack.enter_context(ctx)
                with Progress() as pbar:
                    task = pbar.add_task(f"Generating {result_type} records")
                    for status, record in _validation_gen[self._iter_count]:
                        if status == result_type:
                            yield record
                            pbar.update(task, advance=1)

        self.valid = get_records("valid")
        self.invalid = get_records("invalid")

        return self

    def get_errors(self) -> pd.DataFrame:
        """
        Gets the count of each error type and sets it to the errors attribute.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the count of each error type.
        """
        errors = self.invalid
        self.errors = pd.DataFrame.from_dict(
            Counter([x for x in errors if x("error_type")]),
            orient="index",
            columns=["count"],
        )
        return self.errors

    def errors_json(self):
        """Returns the errors DataFrame as a JSON string."""
        return self.errors.to_json()
