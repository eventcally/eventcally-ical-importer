import datetime

from flask import current_app
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import backref, relationship

from project import db


class Base(db.Model):
    __abstract__ = True

    def update_with_kwargs(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    locale = Column(String(255), nullable=True)

    token_type = Column(String(255))
    access_token = Column(String(255))
    refresh_token = Column(String(255))
    expires_at = Column(Integer())

    configurations = relationship(
        "Configuration",
        primaryjoin="User.id == Configuration.user_id",
        backref=backref("user", lazy=True),
        cascade="all, delete-orphan",
    )

    def to_token(self):
        return dict(
            access_token=self.access_token,
            token_type=self.token_type,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
        )


class Configuration(Base):
    __tablename__ = "configuration"
    _mapper_attrs = [
        "name",
        "organizer_name",
        "place_name",
        "start",
        "description",
        "end",
        "allday",
        "external_link",
    ]
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    title = Column(Unicode(255))
    url = Column(Unicode(255))
    organization_id = Column(Unicode(255))

    name = Column(UnicodeText(), server_default='{{ standard["name"] }}')
    organizer_name = Column(
        UnicodeText(), server_default='{{ standard["organizer_name"] }}'
    )
    place_name = Column(UnicodeText(), server_default='{{ standard["place_name"] }}')
    start = Column(UnicodeText(), server_default='{{ standard["start"] }}')
    description = Column(UnicodeText(), server_default='{{ standard["description"] }}')
    end = Column(UnicodeText(), server_default='{{ standard["end"] }}')
    allday = Column(UnicodeText(), server_default='{{ standard["allday"] }}')
    external_link = Column(
        UnicodeText(), server_default='{{ standard["external_link"] }}'
    )

    runs = relationship(
        "Run",
        primaryjoin="Configuration.id == Run.configuration_id",
        backref=backref("configuration", lazy=True),
        cascade="all, delete-orphan",
        order_by="Run.created_at.desc()",
    )

    imported_events = relationship(
        "ImportedEvent",
        primaryjoin="Configuration.id == ImportedEvent.configuration_id",
        backref=backref("configuration", lazy=True),
        cascade="all, delete-orphan",
        order_by="ImportedEvent.vevent_uid",
    )

    def __init__(self, *args, **kwargs):
        for attr in Configuration._mapper_attrs:
            column = self.__table__.c[attr]
            setattr(self, attr, column.server_default.arg)

        super().__init__(*args, **kwargs)


class ImportedEvent(Base):
    __tablename__ = "importedevent"
    id = Column(Integer, primary_key=True)
    configuration_id = Column(Integer(), ForeignKey("configuration.id"), nullable=False)
    vevent_uid = Column(Unicode(255))
    eventcally_event_id = Column(Unicode(255))
    event = Column(JSONB)

    def get_eventcally_url(self):
        base_url = current_app.config["EVENTCALLY_URL"]
        return f"{base_url}/event/{self.eventcally_event_id}"


class Run(Base):
    __tablename__ = "run"
    id = Column(Integer, primary_key=True)
    configuration_id = Column(Integer(), ForeignKey("configuration.id"), nullable=False)
    configuration_settings = Column(JSONB)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(255))  # success, failure
    failure_event_count = Column(Integer)
    skipped_event_count = Column(Integer)
    new_event_count = Column(Integer)
    updated_event_count = Column(Integer)
    unchanged_event_count = Column(Integer)
    deleted_event_count = Column(Integer)

    log_entries = relationship(
        "LogEntry",
        primaryjoin="Run.id == LogEntry.run_id",
        backref=backref("run", lazy=True),
        cascade="all, delete-orphan",
        order_by="LogEntry.created_at",
    )

    def __init__(self, *args, **kwargs):
        self.created_at = datetime.datetime.utcnow()
        self.failure_event_count = 0
        self.skipped_event_count = 0
        self.new_event_count = 0
        self.updated_event_count = 0
        self.unchanged_event_count = 0
        self.deleted_event_count = 0

        super().__init__(*args, **kwargs)


class LogEntry(Base):
    __tablename__ = "logentry"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer(), ForeignKey("run.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    message = Column(UnicodeText())
    type = Column(String(255))  # vevent
    context = Column(JSONB)
