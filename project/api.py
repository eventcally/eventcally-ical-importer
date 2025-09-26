from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, fields

from project import app
from project.dateutils import berlin_tz, gmt_tz
from project.models import LogEntry, Run

marshmallow = Marshmallow(app)


class SQLAlchemyBaseSchema(marshmallow.SQLAlchemySchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LogEntrySchema(SQLAlchemyBaseSchema):
    class Meta:
        model = LogEntry

    id = marshmallow.auto_field()
    message = marshmallow.auto_field()
    type = marshmallow.auto_field()
    context = marshmallow.auto_field()


class RunSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = Run

    id = marshmallow.auto_field()
    created_at = marshmallow.auto_field()
    status = marshmallow.auto_field()
    failure_event_count = marshmallow.auto_field()
    skipped_event_count = marshmallow.auto_field()
    new_event_count = marshmallow.auto_field()
    updated_event_count = marshmallow.auto_field()
    unchanged_event_count = marshmallow.auto_field()
    deleted_event_count = marshmallow.auto_field()
    log_entries = fields.List(fields.Nested(LogEntrySchema))


class TimezoneDateTimeField(fields.DateTime):
    def __init__(self, format: str | None = None, **kwargs) -> None:
        super().__init__(format, **kwargs)
        self.custom_timezone = kwargs.pop("custom_timezone", None)

    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            if value.tzinfo:
                value = value.astimezone(self.custom_timezone)
            else:
                value = value.replace(tzinfo=self.custom_timezone)

        return super()._serialize(value, attr, obj, **kwargs)

    def deserialize(self, value, attr, data, **kwargs):
        try:
            result = super().deserialize(value, attr, data, **kwargs)
        except ValidationError:
            result = super().deserialize(value + "T00:00:00", attr, data, **kwargs)

        if result and result.tzinfo is None:
            result = self.custom_timezone.localize(result)

        return result


class CustomDateTimeField(TimezoneDateTimeField):
    def __init__(self, format: str | None = None, **kwargs) -> None:
        kwargs["custom_timezone"] = berlin_tz
        super().__init__(format, **kwargs)


class GmtDateTimeField(TimezoneDateTimeField):
    def __init__(self, format: str | None = None, **kwargs) -> None:
        kwargs["custom_timezone"] = gmt_tz
        super().__init__(format, **kwargs)
