from datetime import datetime, timezone
from typing import Annotated, Any, List, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _as_utc(value):
    # The database stores naive UTC; the frontend gets an explicit offset.
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


UtcDateTime = Annotated[datetime, BeforeValidator(_as_utc)]


class ErrorResponse(BaseModel):
    name: str
    message: str


class FieldError(BaseModel):
    loc: List[str]
    msg: str


class ValidationErrorResponse(ErrorResponse):
    errors: List[FieldError]


class ConfigurationListItem(BaseModel):
    id: int
    title: Optional[str] = None
    organization_name: Optional[str] = None


class AppInstallationItem(BaseModel):
    id: int
    organization_name: Optional[str] = None


class ConfigurationList(BaseModel):
    configurations: List[ConfigurationListItem]
    app_installations: List[AppInstallationItem]


class ConfigurationCreate(BaseModel):
    app_installation_id: int


class ConfigurationCreated(BaseModel):
    id: int


class RunListItem(BaseModel):
    id: int
    created_at: Optional[UtcDateTime] = None
    status: Optional[str] = None
    new_event_count: Optional[int] = None
    updated_event_count: Optional[int] = None
    deleted_event_count: Optional[int] = None
    failure_event_count: Optional[int] = None


class ImportedEventItem(BaseModel):
    id: int
    vevent_uid: Optional[str] = None
    eventcally_event_id: Optional[str] = None
    eventcally_url: str
    event: Optional[dict[str, Any]] = None


class ConfigurationDetail(BaseModel):
    id: int
    title: Optional[str] = None
    url: Optional[str] = None
    organization_name: Optional[str] = None
    runs: List[RunListItem]
    imported_events: List[ImportedEventItem]


class ConfigurationForm(BaseModel):
    """The editable fields; the mapper fields are Jinja templates (see `IcalImporter`)."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, max_length=255)
    identifier_tag: str = Field(min_length=1)
    url: Optional[str] = Field(default=None, max_length=255)
    name: str = ""
    organizer_name: str = ""
    place_name: str = ""
    start: str = ""
    description: str = ""
    end: str = ""
    allday: str = ""
    external_link: str = ""
    tags: str = ""
    categories: str = ""
    photo_url: str = ""
    photo_copyright_text: str = ""


class ConfigurationFormRead(BaseModel):
    id: int
    organization_name: Optional[str] = None
    values: ConfigurationForm
    # The mapper fields in display order.
    mapper_fields: List[str]


class LogEntryItem(BaseModel):
    id: Optional[int] = None
    created_at: Optional[UtcDateTime] = None
    message: Optional[str] = None
    type: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class RunCounts(BaseModel):
    status: Optional[str] = None
    failure_event_count: Optional[int] = None
    skipped_event_count: Optional[int] = None
    new_event_count: Optional[int] = None
    updated_event_count: Optional[int] = None
    unchanged_event_count: Optional[int] = None
    deleted_event_count: Optional[int] = None


class RunPreview(RunCounts):
    """The result of a dry run: nothing is stored or sent to EventCally."""

    log_entries: List[LogEntryItem]


class RunDetail(RunCounts):
    id: int
    configuration_id: int
    configuration_title: Optional[str] = None
    created_at: Optional[UtcDateTime] = None
    configuration_settings: Optional[dict[str, Any]] = None
    log_entries: List[LogEntryItem]


class RunJob(BaseModel):
    id: str


class RunJobStatus(BaseModel):
    ready: bool
    successful: Optional[bool] = None
