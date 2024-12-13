from enum import StrEnum
from pydantic.dataclasses import dataclass as pydantic_dataclass


class CityDistrictCodes(StrEnum):
    COUNCIL_DISTRICT: str = "city council"
    MUNICIPALITY: str = "municipality"
    SCHOOL_BOARD: str = "school board"


class CountyDistrictCodes(StrEnum):
    COMMISSIONER: str = "commissioner"
    CONSTABLE: str = "constable"
    SCHOOL_DISTRICT: str = "school district"
    SUB_SCHOOL_DISTRICT: str = "sub school district"
    WATER_DISTRICT: str = "water district"
    MASS_TRANSIT_AUTHORITY: str = "mass transit authority"
    COMMUNITY_COLLEGE: str = "community college"


class StateDistrictCodes(StrEnum):
    LEGISLATIVE_LOWER: str = "legislative lower"
    LEGISLATIVE_UPPER: str = "legislative upper"
    BOARD_OF_EDUCATION: str = "board of education"


class FederalDistrictCodes(StrEnum):
    CONGRESSIONAL: str = "congressional district"


class StateCourtCodes(StrEnum):
    SUPREME_COURT: str = "supreme court"
    CRIMINAL_APPEALS: str = "criminal appeals"
    COURT_OF_APPEALS: str = "court of appeals"


class DistrictCourtCodes(StrEnum):
    CIVIL: str = "civil district court"
    CRIMINAL: str = "criminal district court"
    FAMILY: str = "family district court"


class CountyCourtCodes(StrEnum):
    CONSTITUTIONAL: str = "constitutional court"
    PROBATE: str = "statutory probate court"
    JUSTICE_OF_THE_PEACE: str = "justice of the peace"


class MuncipalCourtCodes(StrEnum):
    TRAFFIC: str = "traffic court"


class SpecialCourtCodes(StrEnum):
    DRUG: str = "drug court"
    VETERANS: str = "veterans court"
    JUVENILE: str = "juvenile court"


@pydantic_dataclass
class PoliticalDistrictCodes:
    CITY: CityDistrictCodes = CityDistrictCodes
    COUNTY: CountyDistrictCodes = CountyDistrictCodes
    STATE: StateDistrictCodes = StateDistrictCodes
    FEDERAL: FederalDistrictCodes = FederalDistrictCodes

@pydantic_dataclass
class CourtDistrictCodes:
    STATE: StateCourtCodes = StateCourtCodes
    DISTRICT: DistrictCourtCodes = DistrictCourtCodes
    COUNTY: CountyCourtCodes = CountyCourtCodes
    MUNICIPAL: MuncipalCourtCodes = MuncipalCourtCodes
    SPECIAL: SpecialCourtCodes = SpecialCourtCodes


@pydantic_dataclass
class DistrictCodes:
    POLITICAL: PoliticalDistrictCodes = PoliticalDistrictCodes
    COURT: CourtDistrictCodes = CourtDistrictCodes