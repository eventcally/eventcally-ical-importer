import traceback

import requests
from ics import Calendar
from jinja2 import BaseLoader, Environment

from project import oauth
from project.api_client import ApiClient
from project.json_client import JsonClient, NotFoundError
from project.models import Configuration, LogEntry, Run


class IcalImporter:
    required_keys = ["name", "organizer_name", "place_name", "start"]

    def __init__(self):
        self.calendar = None
        self.dry = True
        self.run = None
        self.api_client = None
        self.configuration = None

    def load_calendar_data(self, data: str):
        self.calendar = Calendar(data)

    def load_calendar_url(self, url: str):
        self.calendar = Calendar(requests.get(url).text)

    def perform(self, configuration: Configuration):
        self.configuration = configuration
        self.run = Run(status="success")
        template_env = Environment(loader=BaseLoader())
        imported_events = (
            dict(configuration.imported_events)
            if configuration.imported_events
            else dict()
        )

        self.run.configuration_settings = {
            "url": configuration.url,
            "organization_id": configuration.organization_id,
        }

        for attr in Configuration._mapper_attrs:
            self.run.configuration_settings[attr] = getattr(configuration, attr)

        if not self.calendar:
            try:
                self.load_calendar_url(configuration.url)
            except Exception as e:
                self._log(f"Error loading url: {str(e)}")
                self.run.status = "failure"

        if self.calendar:
            uids_to_import = set()

            for vevent in self.calendar.events:
                # Create standard
                standard = dict()
                standard["place_name"] = vevent.location or ""
                standard["organizer_name"] = vevent.organizer or ""
                standard["name"] = vevent.name or ""
                standard["description"] = vevent.description or ""
                standard["start"] = vevent.begin.datetime
                standard["end"] = vevent.end.datetime if vevent.end else None
                standard["allday"] = vevent.all_day
                standard["external_link"] = ""

                # Do the mapping
                event = dict()
                hints = list()
                errors = list()
                for key in standard.keys():
                    if key in configuration._mapper_attrs:
                        try:
                            template_str = getattr(configuration, key)
                            template = template_env.from_string(template_str)
                            event[key] = template.render(
                                standard=standard, vevent=vevent
                            )
                        except Exception as e:
                            errors.append(
                                {
                                    "key": key,
                                    "msg": str(e),
                                }
                            )
                    else:
                        event[key] = standard[key]

                uids_to_import.add(vevent.uid)

                # Check for missing fields
                for required_key in IcalImporter.required_keys:
                    if not event.get(required_key):
                        hints.append(
                            {
                                "key": required_key,
                                "msg": f"Required {required_key} is missing",
                            }
                        )

                # Check if event was imported before and did not change
                imported_event = imported_events.get(vevent.uid)
                event_diff = dict(event)
                if imported_event:
                    event_diff = self._get_event_diff(event, imported_event)

                is_unchanged = False
                is_new = False

                if not event_diff:
                    hints.append(
                        {
                            "msg": "Event did not change since last run",
                        }
                    )
                    self.run.unchanged_event_count = self.run.unchanged_event_count + 1
                    is_unchanged = True
                elif not self.dry:
                    try:
                        event_id, is_inserted = self._send_event_to_eventcally(
                            event, imported_event, event_diff
                        )
                        imported_event = dict(event)
                        imported_event["event_id"] = event_id
                        imported_events[vevent.uid] = imported_event

                        if is_inserted:
                            self.run.new_event_count = self.run.new_event_count + 1
                            is_new = True
                        else:
                            self.run.updated_event_count = (
                                self.run.updated_event_count + 1
                            )
                    except Exception as e:
                        errors.append({"msg": f"{str(e)} {traceback.format_exc()}"})

                if errors:
                    self.run.status = "failure"
                    self.run.failure_event_count = self.run.failure_event_count + 1
                    message = "Fehler beim Einlesen eines Events aus iCal"
                elif hints:
                    self.run.skipped_event_count = self.run.skipped_event_count + 1
                    message = (
                        "Event übersprungen, weil es sich nicht geändert hat"
                        if is_unchanged
                        else "Event übersprungen (s. Hints)"
                    )
                else:
                    message = "Event importiert" if is_new else "Event aktualisiert"

                context = {
                    "vevent": vevent.serialize(),
                    "standard": standard,
                    "event": event,
                    "imported_event": imported_event,
                    "hints": hints,
                    "errors": errors,
                }

                if event_diff:
                    context["diff"] = event_diff
                self._log(message=message, type="vevent", context=context)

            # nicht mehr vorhandene events aus eventcally entfernen
            for imported_uid, imported_event in list(imported_events.items()):
                if imported_uid not in uids_to_import:
                    errors = list()

                    if not self.dry:
                        try:
                            self._ensure_api_client()
                            self.api_client.delete_event(imported_event.get("event_id"))
                            del imported_events[imported_uid]
                        except Exception:
                            errors.append({"msg": traceback.format_exc()})

                    if errors:
                        self.run.status = "failure"
                        self.run.failure_event_count = self.run.failure_event_count + 1
                    else:
                        self.run.deleted_event_count = self.run.deleted_event_count + 1

                    context = {
                        "imported_event": imported_event,
                        "errors": errors,
                    }
                    self._log(message=message, type="deleted", context=context)

        if not self.dry:
            configuration.imported_events = imported_events
            configuration.runs.append(self.run)

    def _ensure_api_client(self):
        if not self.api_client:
            self.api_client = ApiClient(
                JsonClient(oauth.eventcally, self.configuration.user.to_token())
            )
            self.api_client.organization_id = self.configuration.organization_id

    def _send_event_to_eventcally(
        self, event: dict, imported_event: dict, event_diff: dict
    ) -> int:
        self._ensure_api_client()

        # Event
        eventcally_event = dict()

        # Place
        if "place_name" in event_diff:
            place = dict()
            place["name"] = event_diff["place_name"]
            place_id = self.api_client.upsert_place(place)
            eventcally_event["place"] = {"id": place_id}

        # Organizer
        if "organizer_name" in event_diff:
            organizer = dict()
            organizer["name"] = event_diff["organizer_name"]
            organizer_id = self.api_client.upsert_organizer(organizer)
            eventcally_event["organizer"] = {"id": organizer_id}

        # Event
        if "name" in event_diff:
            eventcally_event["name"] = event_diff["name"]

        if "description" in event_diff:
            eventcally_event["description"] = event_diff["description"]

        if "external_link" in event_diff:
            eventcally_event["external_link"] = event_diff["external_link"]

        if "start" in event_diff or "end" in event_diff or "allday" in event_diff:
            eventcally_event["date_definitions"] = [
                {
                    "start": event["start"],
                    "allday": event["allday"],
                }
            ]

            if "end" in event:
                eventcally_event["date_definitions"][0]["end"] = event["end"]

        event_id = imported_event.get("event_id") if imported_event else None
        is_inserted = True
        if event_id:
            try:
                self.api_client.patch_event(event_id, eventcally_event)
                is_inserted = False
            except NotFoundError:
                return self._send_event_to_eventcally(event, None, dict(event))
        else:
            event_id = self.api_client.insert_event(eventcally_event)

        return event_id, is_inserted

    def _get_event_diff(self, event: dict, imported_event: dict) -> dict:
        diff = dict()

        for key, value in event.items():
            if value != imported_event.get(key):
                diff[key] = value

        return diff

    def _log(self, message, **kwargs):
        log_entry = LogEntry(message=message, **kwargs)
        self.run.log_entries.append(log_entry)
