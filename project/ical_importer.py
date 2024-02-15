import traceback

import requests
from ics import Calendar
from jinja2 import BaseLoader, Environment

from project import oauth
from project.api_client import ApiClient
from project.json_client import JsonClient
from project.models import Configuration, ImportedEvent, LogEntry, Run


class IcalImporter:
    required_keys = ["name", "organizer_name", "place_name", "start"]
    tag_configuration_prefix = "ical-importer-cfg-"
    tag_vevent_prefix = "ical-importer-vevent-"

    def __init__(self):
        self.calendar = None
        self.dry = True
        self.run = None
        self.api_client = None
        self.configuration = None
        self.template_env = Environment(loader=BaseLoader())
        self.uids_to_import = None

        self.vevent = None
        self.vevent_standard_mapping = None
        self.vevent_final_mapping = None
        self.vevent_hints = None
        self.vevent_errors = None
        self.vevent_imported_event = None

    def perform(self, configuration: Configuration):
        try:
            self.configuration = configuration
            self._perform()
        except Exception as e:
            self._log(f"Error: {str(e)} {traceback.format_exc()}")
            self.run.status = "failure"

    def _perform(self):
        self._ensure_api_client()
        self._create_run()
        self.uids_to_import = set()

        if not self.dry:
            self._load_events_from_eventcally()

        if not self.calendar:
            self._load_calendar_from_url()

        if not self.calendar:
            return

        for vevent in self.calendar.events:
            self._begin_vevent(vevent)
            self._create_standard_mapping()
            self._create_event_mapping()
            self._check_for_missing_fields()

            if not self.dry and self._check_event_for_changes():
                self._upsert_place()
                self._upsert_organizer()
                self._create_eventcally_event()
                self._send_event_to_eventcally()

            self._end_vevent()

        if not self.dry:
            self._delete_non_existing_events_from_eventcally()
            self.configuration.runs.append(self.run)

    def _load_calendar_from_url(self):
        try:
            self.calendar = Calendar(requests.get(self.configuration.url).text)
            self.calendar_name = next(
                (
                    line.value
                    for line in self.calendar.extra
                    if line.name == "X-WR-CALNAME"
                ),
                None,
            )
        except Exception as e:
            self._log(f"Error loading url: {str(e)}")
            self.run.status = "failure"

    def _create_run(self):
        self.run = Run(status="success")

        self.run.configuration_settings = {
            "url": self.configuration.url,
            "organization_id": self.configuration.organization_id,
        }

        for attr in Configuration._mapper_attrs:
            self.run.configuration_settings[attr] = getattr(self.configuration, attr)

    def _create_standard_mapping(self):
        standard = dict()
        standard["place_name"] = self.vevent.location or ""
        standard["organizer_name"] = self.vevent.organizer or self.calendar_name or ""
        standard["name"] = self.vevent.name or ""
        standard["description"] = self.vevent.description or ""
        standard["start"] = self.vevent.begin.datetime
        standard["end"] = self.vevent.end.datetime if self.vevent.end else None
        standard["allday"] = self.vevent.all_day
        standard["external_link"] = ""

        self.vevent_standard_mapping = standard

    def _begin_vevent(self, vevent):
        self.vevent = vevent
        self.vevent_final_mapping = dict()
        self.vevent_hints = list()
        self.vevent_errors = list()
        self.vevent_imported_event = self._find_imported_event_for_vevent(vevent)
        self.vevent_diff = None
        self.vevent_is_new = True
        self.vevent_is_unchanged = False

    def _end_vevent(self):
        if self.vevent_errors:
            self.run.status = "failure"
            self.run.failure_event_count = self.run.failure_event_count + 1
            message = "Fehler beim Einlesen eines Events aus iCal"
        elif self.vevent_hints:
            self.run.skipped_event_count = self.run.skipped_event_count + 1
            message = (
                "Event übersprungen, weil es sich nicht geändert hat"
                if self.vevent_is_unchanged
                else "Event übersprungen (s. Hints)"
            )
        else:
            message = "Event importiert" if self.vevent_is_new else "Event aktualisiert"

        context = {
            "vevent": self.vevent.serialize(),
            "standard": self.vevent_standard_mapping,
            "event": self.vevent_final_mapping,
            "hints": self.vevent_hints,
            "errors": self.vevent_errors,
        }

        if self.vevent_imported_event:
            context["imported_event"] = {
                "id": self.vevent_imported_event.id,
                "eventcally_event_id": self.vevent_imported_event.eventcally_event_id,
                "vevent_uid": self.vevent_imported_event.vevent_uid,
            }

        if self.vevent_diff:
            context["diff"] = self.vevent_diff

        self._log(message=message, type="vevent", context=context)

    def _create_event_mapping(self):
        for key in self.vevent_standard_mapping.keys():
            if key in self.configuration._mapper_attrs:
                try:
                    template_str = getattr(self.configuration, key)
                    template = self.template_env.from_string(template_str)
                    self.vevent_final_mapping[key] = template.render(
                        standard=self.vevent_standard_mapping, vevent=self.vevent
                    )
                except Exception as e:
                    self.vevent_errors.append(
                        {
                            "key": key,
                            "msg": str(e),
                        }
                    )
            else:
                self.vevent_final_mapping[key] = self.vevent_standard_mapping[key]

        self.uids_to_import.add(self.vevent.uid)

    def _check_for_missing_fields(self):
        for required_key in IcalImporter.required_keys:
            if not self.vevent_final_mapping.get(required_key):
                self.vevent_hints.append(
                    {
                        "key": required_key,
                        "msg": f"Required {required_key} is missing",
                    }
                )

    def _find_imported_event_for_vevent(self, vevent) -> ImportedEvent:
        return next(
            (
                i
                for i in self.configuration.imported_events
                if i.vevent_uid == vevent.uid
            ),
            None,
        )

    def _upsert_place(self):
        place_name = self.vevent_final_mapping["place_name"]
        self.vevent_place_id = next(
            (p["id"] for p in self.eventcally_places if p["name"] == place_name),
            None,
        )

        if self.vevent_place_id:
            return

        self.vevent_place_id = self.api_client.upsert_place({"name": place_name})
        self.eventcally_places.append({"id": self.vevent_place_id, "name": place_name})

    def _upsert_organizer(self):
        organizer_name = self.vevent_final_mapping["organizer_name"]
        self.vevent_organizer_id = next(
            (
                o["id"]
                for o in self.eventcally_organizers
                if o["name"] == organizer_name
            ),
            None,
        )

        if self.vevent_organizer_id:
            return

        self.vevent_organizer_id = self.api_client.upsert_organizer(
            {"name": organizer_name}
        )
        self.eventcally_organizers.append(
            {"id": self.vevent_organizer_id, "name": organizer_name}
        )

    def _create_eventcally_event(self):
        eventcally_event = dict()
        eventcally_event["tags"] = self._get_event_tags()
        eventcally_event["place"] = {"id": self.vevent_place_id}
        eventcally_event["organizer"] = {"id": self.vevent_organizer_id}
        eventcally_event["name"] = self.vevent_final_mapping["name"]
        eventcally_event["description"] = self.vevent_final_mapping["description"]
        eventcally_event["external_link"] = self.vevent_final_mapping["external_link"]

        eventcally_event["date_definitions"] = [
            {
                "start": self.vevent_final_mapping["start"],
                "allday": self.vevent_final_mapping["allday"],
            }
        ]

        if "end" in self.vevent_final_mapping:
            eventcally_event["date_definitions"][0]["end"] = self.vevent_final_mapping[
                "end"
            ]

        self.vevent_eventcally_event = eventcally_event

    def _ensure_api_client(self):
        if not self.api_client:
            self.api_client = ApiClient(
                JsonClient(oauth.eventcally, self.configuration.user.to_token())
            )
            self.api_client.organization_id = self.configuration.organization_id

    def _load_events_from_eventcally(self):
        tag = self._get_configuration_event_tag()
        events = self.api_client.find_events_by_tag(tag)

        to_remove_from_imported_events = list(self.configuration.imported_events)
        self.eventcally_places = []
        self.eventcally_organizers = []

        for event in events:
            tags = event["tags"].split(",")
            vevent_tag = next(
                (tag for tag in tags if tag.startswith(IcalImporter.tag_vevent_prefix)),
                None,
            )

            if not vevent_tag:
                continue

            vevent_uid = vevent_tag.split(IcalImporter.tag_vevent_prefix)[1]

            if not vevent_uid:
                continue

            imported_event = next(
                (
                    i
                    for i in self.configuration.imported_events
                    if i.vevent_uid == vevent_uid
                ),
                None,
            )
            if imported_event:
                to_remove_from_imported_events.remove(imported_event)
            else:
                self._append_imported_event(vevent_uid, event["id"], None)

            self.eventcally_places.append(dict(event["place"]))
            self.eventcally_organizers.append(dict(event["organizer"]))

        for to_remove in to_remove_from_imported_events:
            self.configuration.imported_events.remove(to_remove)

    def _append_imported_event(
        self, vevent_uid: str, eventcally_event_id: int, event: dict
    ) -> ImportedEvent:
        imported_event = ImportedEvent()
        imported_event.vevent_uid = vevent_uid
        imported_event.eventcally_event_id = eventcally_event_id
        imported_event.event = event
        self.configuration.imported_events.append(imported_event)
        return imported_event

    def _send_event_to_eventcally(self):
        if self.vevent_imported_event:
            self._send_event_update_to_eventcally()
            return

        self._send_event_create_to_eventcally()

    def _send_event_create_to_eventcally(self):
        try:
            eventcally_event_id = self.api_client.insert_event(
                self.vevent_eventcally_event
            )
        except Exception as e:
            self.vevent_errors.append({"msg": f"{str(e)} {traceback.format_exc()}"})
            return

        self.vevent_imported_event = self._append_imported_event(
            self.vevent.uid, eventcally_event_id, self.vevent_final_mapping
        )
        self.vevent_is_new = True
        self.run.new_event_count += 1

    def _send_event_update_to_eventcally(self):
        try:
            self.api_client.update_event(
                self.vevent_imported_event.eventcally_event_id,
                self.vevent_eventcally_event,
            )
            self.vevent_imported_event.event = self.vevent_final_mapping
        except Exception as e:
            self.vevent_errors.append({"msg": f"{str(e)} {traceback.format_exc()}"})
            return

        self.vevent_is_new = False
        self.run.updated_event_count += 1

    def _delete_non_existing_events_from_eventcally(self):
        to_remove_from_imported_events = list()
        for imported_event in self.configuration.imported_events:
            if imported_event.vevent_uid not in self.uids_to_import:
                errors = list()

                try:
                    self.api_client.delete_event(imported_event.eventcally_event_id)
                    to_remove_from_imported_events.append(imported_event)
                except Exception:
                    errors.append({"msg": traceback.format_exc()})

                if errors:
                    self.run.status = "failure"
                    self.run.failure_event_count += 1
                else:
                    self.run.deleted_event_count += 1

                context = {
                    "imported_event": {
                        "id": imported_event.id,
                        "eventcally_event_id": imported_event.eventcally_event_id,
                        "vevent_uid": imported_event.vevent_uid,
                        "event": imported_event.event,
                    },
                    "errors": errors,
                }
                self._log(message="Event gelöscht", type="deleted", context=context)

        for to_remove in to_remove_from_imported_events:
            self.configuration.imported_events.remove(to_remove)

    def _check_event_for_changes(self):
        self._create_event_diff()
        self.vevent_is_unchanged = not self.vevent_diff

        if self.vevent_is_unchanged:
            self.vevent_hints.append(
                {
                    "msg": "Event did not change since last run",
                }
            )
            self.run.unchanged_event_count += 1

        return not self.vevent_is_unchanged

    def _create_event_diff(self):
        if not self.vevent_imported_event or not self.vevent_imported_event.event:
            self.vevent_diff = dict(self.vevent_final_mapping)
            return

        diff = dict()

        for key, value in self.vevent_final_mapping.items():
            if value != self.vevent_imported_event.event.get(key):
                diff[key] = value

        self.vevent_diff = diff

    def _log(self, message, **kwargs):
        log_entry = LogEntry(message=message, **kwargs)
        self.run.log_entries.append(log_entry)

    def _get_event_tags(self):
        return f"{self._get_configuration_event_tag()},{self._get_vevent_event_tag()}"

    def _get_configuration_event_tag(self):
        return f"{IcalImporter.tag_configuration_prefix}{self.configuration.identifier_tag.replace(',','')}"

    def _get_vevent_event_tag(self):
        return f"{IcalImporter.tag_vevent_prefix}{self.vevent.uid.replace(',','')}"
