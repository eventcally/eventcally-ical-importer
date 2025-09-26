import datetime
import uuid

from flask import current_app
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, declared_attr, deferred, relationship

from project import current_user, db
from project.dateutils import gmt_tz


def current_user_id_or_none():
    return current_user.id if current_user else None


class TrackableMixin(object):
    @declared_attr
    def created_at(cls):
        return deferred(
            Column(DateTime, default=datetime.datetime.utcnow), group="trackable"
        )

    @declared_attr
    def updated_at(cls):
        return deferred(
            Column(
                DateTime,
                onupdate=datetime.datetime.utcnow,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by_id(cls):
        return deferred(
            Column(
                "created_by_id",
                ForeignKey("user.id", ondelete="SET NULL"),
                default=current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by(cls):
        return relationship(
            "User",
            primaryjoin="User.id == %s.created_by_id" % cls.__name__,
            remote_side="User.id",
            backref=backref("created_%s" % cls.__tablename__, lazy=True),
        )

    @declared_attr
    def updated_by_id(cls):
        return deferred(
            Column(
                "updated_by_id",
                ForeignKey("user.id", ondelete="SET NULL"),
                onupdate=current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def updated_by(cls):
        return relationship(
            "User",
            primaryjoin="User.id == %s.updated_by_id" % cls.__name__,
            remote_side="User.id",
            backref=backref("updated_%s" % cls.__tablename__, lazy=True),
        )

    @hybrid_property
    def last_modified_at(self):
        return self.updated_at if self.updated_at else self.created_at

    @last_modified_at.expression
    def last_modified_at(cls):
        return func.coalesce(cls.updated_at, cls.created_at)

    @property
    def created_by_label(self):
        if self.created_by:
            return self.created_by.email

        return None  # pragma: no cover

    @property
    def updated_by_label(self):
        if self.updated_by:
            return self.updated_by.email

        return None  # pragma: no cover

    def get_hash(self):
        return (
            int(self.last_modified_at.replace(tzinfo=gmt_tz).timestamp() * 1000)
            if self.last_modified_at
            else 0
        )


class Base(db.Model):
    __abstract__ = True

    def update_with_kwargs(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    last_app_installations_sync = Column(DateTime)


class UserAppInstallations(db.Model):
    __tablename__ = "user_app_installations"
    __table_args__ = (UniqueConstraint("user_id", "app_installation_id"),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    app_installation_id = db.Column(
        db.Integer, db.ForeignKey("app_installation.id"), nullable=False
    )


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    eventcally_id = Column(Unicode(255), unique=True)
    email = Column(String(255), unique=True)
    locale = Column(String(255), nullable=True)

    token_type = Column(String(255))
    access_token = Column(String(255))
    refresh_token = Column(String(255))
    expires_at = Column(Integer())

    token_created_at = Column(DateTime)
    last_token_check = Column(DateTime)
    last_app_installations_sync = Column(DateTime)

    app_installations = relationship(
        "AppInstallation",
        secondary="user_app_installations",
        backref=backref("users", lazy=True),
    )

    def to_token(self):
        return dict(
            access_token=self.access_token,
            token_type=self.token_type,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
        )


class AppInstallation(Base):
    __tablename__ = "app_installation"
    id = Column(Integer, primary_key=True)
    eventcally_id = Column(Unicode(255), unique=True)
    organization_id = Column(Unicode(255))
    organization_name = Column(Unicode(255))
    permissions = Column(UnicodeText)

    configurations = relationship(
        "Configuration",
        primaryjoin="AppInstallation.id == Configuration.app_installation_id",
        backref=backref("app_installation", lazy=True),
        cascade="all, delete-orphan",
    )


def generate_uuid():
    return str(uuid.uuid4())


class Configuration(Base, TrackableMixin):
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
        "tags",
        "categories",
        "photo_url",
        "photo_copyright_text",
    ]
    id = Column(Integer, primary_key=True)

    app_installation_id = Column(
        Integer(), ForeignKey("app_installation.id"), nullable=False
    )

    title = Column(Unicode(255))
    url = Column(Unicode(255))
    identifier_tag = Column(String, default=generate_uuid)

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
    photo_url = Column(UnicodeText(), server_default='{{ standard["photo_url"] }}')
    photo_copyright_text = Column(
        UnicodeText(), server_default='{{ standard["photo_copyright_text"] }}'
    )
    categories = Column(UnicodeText(), server_default='{{ standard["categories"] }}')
    tags = Column(UnicodeText(), server_default='{{ standard["tags"] }}')

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

    @property
    def organization_id(self):
        return self.app_installation.organization_id

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
