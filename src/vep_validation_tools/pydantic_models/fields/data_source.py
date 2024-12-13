from datetime import date

from sqlmodel import Field as SQLModelField, Relationship
from sqlalchemy import func

from ..model_bases import SQLModelBase

"""
class DataSourceLink(SQLModelBase, table=True):
    data_source_id: str | None = SQLModelField(
        default=None,
        foreign_key="datasource.file",
        primary_key=True)
    record_id: int | None = SQLModelField(
        default=None,
        foreign_key=f'recordbasemodel.id',
        primary_key=True)
"""


class DataSource(SQLModelBase, table=True):
    file: str = SQLModelField(..., description="Name of the file", primary_key=True)
    processed_date: date | None = SQLModelField(default=None,
                                                description="Date the file was processed",
                                                sa_column_kwargs={"server_default": func.current_date()}
                                                )
    records: list['RecordBaseModel'] = Relationship(
        back_populates='data_source',)
        # link_model=DataSourceLink)

    def __hash__(self):
        return hash(self.file)

# class DataSourceModel(Base):
#     __abstract__ = True
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     file: Mapped[str] = mapped_column(String, nullable=False, unique=True)
#     processed_date: Mapped[Date] = mapped_column(Date, nullable=False)
#     record_count: Mapped[int] = mapped_column(Integer, default=0)
#
#     def __hash__(self):
#         return hash(self.file)
#
#     @declared_attr
#     @abc.abstractmethod
#     def record(cls):
#         return relationship('RecordModel', back_populates='data_sources')
