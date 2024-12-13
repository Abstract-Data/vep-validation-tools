from sqlmodel import Field as SQLModelField, Relationship

from ..model_bases import SQLModelBase


class VEPMatch(SQLModelBase, table=True):
    __tablename__ = 'vep_match'
    id: int | None = SQLModelField(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    uuid: str | None = SQLModelField(default=None)
    long: str | None = SQLModelField(default=None)
    short: str | None = SQLModelField(default=None)
    name_dob: str | None = SQLModelField(default=None)
    addr_text: str | None = SQLModelField(default=None)
    addr_key: str | None = SQLModelField(default=None)
    full_key: str | None = SQLModelField(default=None)
    full_key_hash: str | None = SQLModelField(default=None)
    best_key: str | None = SQLModelField(default=None)
    uses_mailzip: bool | None = SQLModelField(default=None)
    records: 'RecordBaseModel' = Relationship(back_populates='vep_keys')
    