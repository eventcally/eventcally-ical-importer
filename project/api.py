from flask_marshmallow import Marshmallow
from marshmallow import fields

from project import app
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
