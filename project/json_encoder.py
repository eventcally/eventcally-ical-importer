from datetime import date, datetime

from flask.json.provider import DefaultJSONProvider


class CustomJsonProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        return super(CustomJsonProvider, CustomJsonProvider).default(
            obj
        )  # pragma: no cover
