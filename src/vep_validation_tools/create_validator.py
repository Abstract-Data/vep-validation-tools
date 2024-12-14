from dataclasses import field, dataclass
from typing import Tuple, Iterable, Dict, Any, Optional, Generator

from sqlmodel import SQLModel, Relationship, Field as SQLModelField, Session, select
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError

from .abcs.create_validator_abc import (
    CreateValidatorABC,
    RunValidationOutput,
    ErrorDetails
)
from .pydantic_models.rename_model import RecordRenamer
from .pydantic_models.cleanup_model import (
    PreValidationCleanUp,
    PersonName,
    VendorName,
    VendorTags,
    VendorTagsToVendorToRecordLink,
    VendorTagsToVendorLink,
    VoterRegistration,
    Address,
    AddressLink,
    ValidatedPhoneNumber,
    DataSource,
    District,
    InputData,
    VEPMatch,
    PhoneLink,
    ElectionList,
    ElectionTurnoutCalculator
)
from .pydantic_models.record import RecordBaseModel


class RecordRenameValidator(CreateValidatorABC):
    validator: RecordRenamer


class CleanUpRecordValidator(CreateValidatorABC):
    validator: PreValidationCleanUp = field(default=PreValidationCleanUp)


class FinalValidation(CreateValidatorABC):
    validator: RecordBaseModel


# @dataclass
# class CreateValidator:
#     state_name: Tuple[str, str]
#     renaming_validator: RecordRenamer | RecordRenameValidator
#     record_validator: RecordBaseModel | FinalValidation
#     cleanup_validator: CleanUpRecordValidator | PreValidationCleanUp = field(default=PreValidationCleanUp)
#     _records: Optional[Iterable[Dict[str, Any]]] = field(default=None, init=False)
#     _validation_pipeline: Optional[Generator[RunValidationOutput]] = field(default=None, init=False)
#
#     def __post_init__(self):
#         self.renaming_validator = RecordRenameValidator(self.state_name, self.renaming_validator)
#         self.record_validator = FinalValidation(self.state_name, self.record_validator)
#         self.cleanup_validator = CleanUpRecordValidator(self.state_name, self.cleanup_validator)
#
#     @property
#     def valid(self) -> Generator[ValidatorConfig, None, None]:
#         if self._validation_pipeline is None:
#             raise ValueError("run_validation must be called before accessing valid records")
#         for status, record in self._validation_pipeline:
#             if status == 'valid':
#                 yield record
#             if status == 'invalid':
#                 self.renaming_validator._invalid_count += 1
#
#     @property
#     def invalid(self) -> Generator[Dict[str, Any], None, None]:
#         if self._validation_pipeline is None:
#             raise ValueError("run_validation must be called before accessing invalid records")
#         for status, record in self._validation_pipeline:
#             if status == 'invalid':
#                 yield record
#             if status == 'valid':
#                 self.renaming_validator._valid_count += 1
#
#     def validate_single_record(self, record: Dict[str, Any]) -> Tuple[str, Any]:
#         renamed_record_gen = self.renaming_validator.validate_single_record(record)
#         renamed_result = next(renamed_record_gen)
#         if renamed_result[0] == 'valid':
#             renamed_dict = dict(renamed_result[1])
#             renamed_dict['data'] = renamed_result[1]
#             cleaned_record_gen = self.cleanup_validator.validate_single_record(renamed_dict)
#             cleaned_result = next(cleaned_record_gen)
#             if cleaned_result[0] == 'valid':
#                 final_record_gen = self.record_validator.validate_single_record(dict(cleaned_result[1]))
#                 final_result = next(final_record_gen)
#                 return final_result
#             else:
#                 return 'invalid', ErrorDetails(
#                     model=self.cleanup_validator.__class__.__name__,
#                     point_of_failure="cleanup",
#                     errors=cleaned_result[1].errors
#                 )
#         else:
#             return 'invalid', ErrorDetails(
#                 model=self.renaming_validator.__class__.__name__,
#                 point_of_failure="rename",
#                 errors=renamed_result[1].errors
#             )
#
#     def create_validation_pipeline(self) -> Generator[RunValidationOutput]:
#         if self._records is None:
#             raise ValueError("run_validation must be called before creating the validation pipeline")
#
#         with ThreadPoolExecutor() as executor:
#             futures = (executor.submit(self.validate_single_record, record) for record in self._records)
#             for future in as_completed(futures):
#                 yield future.result()
#
#     def run_validation(self, records: Iterable[Dict[str, Any]]) -> None:
#         self._records = records
#         self._validation_pipeline = self.create_validation_pipeline()
#
#     def get_error_summary(self) -> Dict[str, int]:
#         error_summary = {}
#         for validator in [self.renaming_validator, self.cleanup_validator, self.record_validator]:
#             for error in validator.invalid:
#                 error_type = error['error_type']
#                 error_summary[error_type] = error_summary.get(error_type, 0) + 1
#         return error_summary


@dataclass
class CreateValidator:
    state_name: Tuple[str, str]
    renaming_validator: RecordRenamer | RecordRenameValidator
    record_validator: RecordBaseModel | FinalValidation
    cleanup_validator: PreValidationCleanUp | CleanUpRecordValidator = field(default=PreValidationCleanUp)
    _records: Optional[Iterable[Dict[str, Any]]] = field(default=None, init=False)
    _validation_pipeline: Optional[Generator[RunValidationOutput, None, None]] = field(default=None, init=False)

    def __post_init__(self):
        self._set_table_names()
        self.renaming_validator = RecordRenameValidator(self.state_name, self.renaming_validator)
        self.record_validator = FinalValidation(self.state_name, self.record_validator)
        self.cleanup_validator = CleanUpRecordValidator(self.state_name, self.cleanup_validator)

    @property
    def valid(self) -> Generator[PreValidationCleanUp, None, None]:
        if self._validation_pipeline:
            # raise ValueError("run_validation must be called before accessing valid records")
            for status, record in self._validation_pipeline:
                if status == 'valid':
                    # self._handle_collected_groups(record)
                    yield record
                if status == 'invalid':
                    self.renaming_validator._invalid_count += 1

    @property
    def invalid(self) -> Generator[Dict[str, Any], None, None]:
        if self._validation_pipeline:
            # raise ValueError("run_validation must be called before accessing invalid records")
            for status, record in self._validation_pipeline:
                if status == 'invalid':
                    # self._handle_collected_groups(record)
                    yield record
                if status == 'valid':
                    self.renaming_validator._valid_count += 1

    def _set_table_names(self):
        for table_name, table in SQLModel.metadata.tables.items():
            old_name = table.name
            new_name = f"voterfile_{old_name}"
            table.name = new_name

    def validate_single_record(self, record: Dict[str, Any]) -> Generator[Tuple[str, Any], None, None]:
        renamed_record_gen = self.renaming_validator.validate_single_record(record)
        renamed_result = next(renamed_record_gen)
        if renamed_result[0] == 'valid':
            renamed_dict = dict(renamed_result[1])
            renamed_dict['data'] = renamed_result[1]
            cleaned_record_gen = self.cleanup_validator.validate_single_record(renamed_dict)
            cleaned_result = next(cleaned_record_gen)
            if cleaned_result[0] == 'valid':
                # # self._handle_collected_groups(cleaned_result)
                # final_record_gen = self.record_validator.validate_single_record(dict(cleaned_result[1]))
                # final_result = next(final_record_gen)
                # _container.final_model = final_result[1]
                yield "valid", cleaned_result[1]
            else:
                yield 'invalid', ErrorDetails(
                    model=self.cleanup_validator.__class__.__name__,
                    point_of_failure="cleanup",
                    errors=cleaned_result[1].errors
                )
        else:
            yield 'invalid', ErrorDetails(
                model=self.renaming_validator.__class__.__name__,
                point_of_failure="rename",
                errors=renamed_result[1].errors
            )

    def create_validation_pipeline(self) -> Generator[RunValidationOutput, None, None]:
        if self._records is None:
            raise ValueError("run_validation must be called before creating the validation pipeline")

        # with ThreadPoolExecutor() as executor:
        #     futures = [executor.submit(self.validate_single_record, record) for record in self._records]
        #     for future in as_completed(futures):
        #         yield from future.result()

        for record in self._records:
            yield from self.validate_single_record(record)

    def run_validation(self, records: Iterable[Dict[str, Any]]) -> None:
        self._records = records
        self._validation_pipeline = self.create_validation_pipeline()

    def get_error_summary(self) -> Dict[str, int]:
        error_summary = {}
        for validator in [self.renaming_validator, self.cleanup_validator, self.record_validator]:
            for error in validator.invalid:
                error_type = error['error_type']
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
        return error_summary


@dataclass
class CreateRecords:
    engine: Optional[Engine] = None
    records: list[RecordBaseModel] = field(default_factory=list)
    errors: list[PreValidationCleanUp] = field(default_factory=list)
    elections: ElectionList = field(default_factory=ElectionList)

    def _get_or_create_person_name(self, person_name: PersonName, session: Session) -> PersonName:
        existing = session.execute(
            select(PersonName).where(PersonName.id == person_name.id)
        ).scalar_one_or_none()

        if existing:
            return session.merge(person_name)
        else:
            session.add(person_name)
            session.flush()
            return person_name


    def _get_or_create_election(self, election: "ElectionTypeDetails", session: Session) -> "ElectionTypeDetails":
        """Get existing election or create a new one if it doesn't exist."""
        existing = session.execute(
            select(type(election)).where(type(election).id == election.id)
        ).scalar_one_or_none()

        if existing:
            # Update existing election with any new information
            if election.dates and not existing.dates:
                existing.dates = election.dates
            if election.desc and not existing.desc:
                existing.desc = election.desc
            return existing
        else:
            session.add(election)
            return election

    def _get_or_create_vote_method(self, vote_method: "VoteMethod", election: "ElectionTypeDetails",
                                   session: Session) -> "VoteMethod":
        """Get existing vote method or create a new one if it doesn't exist."""
        existing = next(
            (vm for vm in election.election_vote_methods if vm.id == vote_method.id),
            None
        )
        if existing:
            return existing
        else:
            election.election_vote_methods.append(vote_method)
            session.add(vote_method)
            return vote_method

    def _get_or_create_district_list(self, district_list: "FileDistrictList", session: Session) -> "FileDistrictList":
        existing = session.execute(
            select(type(district_list)).where(type(district_list).id == district_list.id)
        ).scalar_one_or_none()

        if existing:
            session.merge(district_list)
            return existing
        else:
            session.add(district_list)
            return district_list

    def _get_or_create_address(self, address: Address, session: Session) -> "Address":
        existing = session.execute(
            select(Address).where(Address.id == address.id)
        ).scalar_one_or_none()

        if existing:
            return existing
        else:
            session.add(address)
            session.flush()
            return address

    def _get_or_create_data_source(self, data_source: "DataSource", session: Session) -> "DataSource":
        existing = session.execute(
            select(type(data_source)).where(type(data_source).file == data_source.file)
        ).scalar_one_or_none()

        if existing:
            return existing
        else:
            session.add(data_source)
            session.flush()
            return data_source

    def _each_record_cleanup(self, data: PreValidationCleanUp, session: Session) -> RecordBaseModel:
        error_count = 0
        try:
            session.add_all([data.voter_registration, data.input_data])
            _districts = self._get_or_create_district_list(data.district_set, session)
            _person_name = self._get_or_create_person_name(data.name, session)
            _data_source = [self._get_or_create_data_source(x, session) for x in data.data_source][0]

            record = RecordBaseModel(
                name_id=_person_name.id,
                name=_person_name,
                voter_registration_id=data.voter_registration.vuid,
                district_set_id=_districts.id,
                input_data_id=data.input_data.id,
                data_source_id=_data_source.file,
                voter_registration=data.voter_registration,
                input_data=data.input_data,
                district_set=_districts,
                data_source=_data_source
            )
            session.add(record)
            # record.data_source = [self._get_or_create_data_source(x, session) for x in data.data_source][0]
            if data.vep_keys:
                record.vep_keys_id = data.vep_keys.id
                record.vep_keys = data.vep_keys

            addresses = list(set(self._get_or_create_address(address, session) for address in data.address_list))
            record.address_list.extend(addresses)
            for e in data.elections:
                election = self._get_or_create_election(e.election, session)
                vote_method = self._get_or_create_vote_method(e.vote_method, election, session)

                # Create the vote record
                vote_record = e.vote_record
                vote_record.election = election
                vote_record.vote_method = vote_method
                record.vote_history.append(vote_record)
                self.elections.add_or_update_election(
                    election=election,
                    vote_method=vote_method,
                    vote_record=vote_record
                )
            session.add(record)
            session.commit()
            return record

        except IntegrityError as e:
            session.rollback()
            error_count += 1
            self.errors.append(data)


    def create_db_records(self, records: Iterable[PreValidationCleanUp]) -> None:
        with Session(self.engine) as session:
            with session.no_autoflush:
                for i, record in enumerate(records, 1):
                    try:
                        self._each_record_cleanup(record, session)
                        if i % 10000 == 0:
                            print(f"Processed {i:,} records")
                    except Exception as e:
                        print(f"Error processing record {i}: {str(e)}")
                        continue  # Skip failed records and continue with the next one

    def _create_non_db_record(self, record: PreValidationCleanUp) -> RecordBaseModel:
        for e in record.elections:
            self.elections.add_or_update_election(e.election, e.vote_method, e.vote_record)

        # _turnout_calc = ElectionTurnoutCalculator()
        # _election_score = _turnout_calc.calculate_scores(
        #     elections_voter_voted_in=record.elections,
        #     all_elections=self.elections
        # )
        return RecordBaseModel(
            name_id=record.name.id,
            voter_registration_id=record.voter_registration.vuid,
            district_set_id=record.district_set.id,
            input_data_id=record.input_data.id,
            name=record.name,
            voter_registration=record.voter_registration,
            district_set=record.district_set,
            address_list=record.address_list,
            phone=record.phone,
            data_source=record.data_source[0],
            input_data=record.input_data,
            vep_keys=record.vep_keys,
            vote_history=[x.vote_record for x in record.elections],
            # election_scores=_election_score
        )

    def election_generator(self, records: Iterable[PreValidationCleanUp]):
        for record in records:
            for e in record.elections:
                self.elections.add_or_update_election(e.election, e.vote_method, e.vote_record)


    def create_records(self, records: Iterable[PreValidationCleanUp]) -> Generator[RecordBaseModel, None, None]:
        # self.election_generator(records)
        for record in records:
            yield self._create_non_db_record(record)

