from datetime import datetime, date

from pydantic_core import PydanticCustomError
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass
class DateValidators:

    @staticmethod
    def validate_date_dob(self):
        _date_format = self.date_format

        if not _date_format:
            raise PydanticCustomError(
                'missing_date_format',
                'Date format is missing for voter registration date',
                dict(
                    model='PreValidationCleanUp',
                    function='validate_dob',
                    nested_function='validate_date_dob'
                )
            )
        _dob = None
        valid_dob = None
        dob_corrections = []
        if not self.data.person_dob:
            if self.data.person_dob_yearmonth:
                if self.data.person_dob_day:
                    _dob = f"{self.data.person_dob_yearmonth}{self.data.person_dob_day}"
                else:
                    _dob = self.data.person_dob = f"{self.data.person_dob_yearmonth}01"
                    dob_corrections.append('Combined yearmonth and day values to create a valid date')
            elif self.data.person_dob_year:
                if self.data.person_dob_month and self.data.person_dob_day:
                    _dob = f"{self.data.person_dob_year}{self.data.person_dob_month}{self.data.person_dob_day}"
                    dob_corrections.append('Combined year, month, and day values to create a valid date')
                elif self.data.person_dob_month:
                    _dob = f"{self.data.person_dob_year}{self.data.person_dob_month}01"
                    dob_corrections.append('Combined year and month values to create a valid date')
                else:
                    _dob = f"{self.data.person_dob_year}0101"
                    dob_corrections.append('Combined year and month values to create a valid date')
            else:
                _dob = None

        if self.data.person_dob:
            if isinstance(self.data.person_dob, date):
                valid_dob = self.data.person_dob
            elif isinstance(self.data.person_dob, str):
                _dob = str(self.data.person_dob).replace('-', '')
                if len(_dob) == 6 and '%Y%m%d' in _date_format:
                    dob_corrections.append(
                        "DOB only has 6 characters. Attempting to validate by adding 01 for the day.")
                    _dob = f"{_dob}01"
            else:
                _dob = None
                dob_corrections.append('DOB is not a valid date. Removed DOB.')

        if _dob:

            if _dob[-2:] == '00':
                _dob = _dob[:-2] + '01'
            if isinstance(_date_format, list):
                for _time_format in _date_format:
                    try:
                        valid_dob = datetime.strptime(_dob, _time_format).date()
                    except ValueError:
                        continue
                    else:
                        break
            elif isinstance(_date_format, str):
                valid_dob = datetime.strptime(_dob, _date_format).date()
            else:
                valid_dob = None
            self.person_details['person_dob'] = valid_dob
            dob_corrections.append('Converted values to a valid date')
            self.corrected_errors.update({'dob': dob_corrections})
        return self

    @staticmethod
    def validate_date_edr(self):
        _date_format = self.date_format
        _voter_registration = self.data.voter_registration_date
        _voter_registration_corrections = []

        if not _voter_registration:
            return self

        if not _date_format:
            raise PydanticCustomError(
                'missing_date_format',
                'Date format is missing for voter registration date',
                dict(
                    model='PreValidationCleanUp',
                    function='validate_edr',
                    nested_function='validate_date_edr'
                )
            )

        # _possible_keys = key_list_with_suffix('registration_date', _voter_registration)
        # if _possible_keys and len(_possible_keys) == 1:
        #     if _date_format:
        if isinstance(_date_format, list):
            for _time_format in _date_format:
                try:
                    self.input_voter_registration['edr'] = (
                        datetime.strptime(
                            _voter_registration, _time_format
                        ).date()
                    )
                except ValueError:
                    continue
                else:
                    break
        elif isinstance(_date_format, str):
            try:
                self.input_voter_registration['edr'] = (
                    datetime.strptime(
                        _voter_registration, _date_format
                    ).date()
                )
                _voter_registration_corrections.append('Converted registration to a valid date')
            except ValueError:
                raise PydanticCustomError(
                    'invalid_registration_date',
                    'Invalid voter registration date for record: {voter_registration_date}',
                    dict(
                        model='PreValidationCleanUp',
                        function='validate_edr',
                        nested_function='validate_date_edr',
                        voter_registration_date=_voter_registration)
                )
            self.corrected_errors.update({'voter_registration': _voter_registration_corrections})
            if not self.input_voter_registration['edr'] and self.data.settings.get('FILE-TYPE') == 'voterfile':
                raise PydanticCustomError(
                    'invalid_registration_date',
                    'Invalid voter registration date for record: {voter_registration_date}',
                    dict(
                        model='PreValidationCleanUp',
                        function='validate_edr',
                        nested_function='validate_date_edr',
                        voter_registration_date=_voter_registration)
                )
        return self