from project import app
from project.json_client import JsonClient, NotFoundError, UnprocessableEntityError


class ApiClient:
    def __init__(self, json_client: JsonClient):
        self.json_client = json_client
        self.organization_id = None

    def get_categories(self) -> int:
        app.logger.debug("Get categories")
        response = self.json_client.get("/event-categories?per_page=50")
        pagination = response.json()
        return pagination["items"]

    def insert_organizer(self, data: dict) -> int:
        app.logger.debug(f"Insert organizer {data['name']}")
        response = self.json_client.post(
            f"/organizations/{self.organization_id}/organizers", data=data
        )
        organizer = response.json()
        return organizer["id"]

    def update_organizer(self, organizer_id: int, data: dict):
        app.logger.debug(f"Update organizer {organizer_id} {data['name']}")
        self.json_client.put(f"/organizers/{organizer_id}", data=data)

    def upsert_organizer(self, data: dict) -> int:
        name = data["name"]
        app.logger.debug(f"Upsert organizer {name}")
        response = self.json_client.get(
            f"/organizations/{self.organization_id}/organizers?name={name}"
        )
        pagination = response.json()
        organizer = self._find_item_in_pagination(pagination, name)

        if not organizer:
            app.logger.debug(f"Organizer {name} does not exist")
            return self.insert_organizer(data)

        organizer_id = organizer["id"]
        app.logger.debug(
            f"Organizer {organizer_id} {name} already exists. No need to update."
        )
        return organizer_id

    def insert_place(self, data: dict) -> int:
        app.logger.debug(f"Insert place {data['name']}")
        response = self.json_client.post(
            f"/organizations/{self.organization_id}/places", data=data
        )
        place = response.json()
        return place["id"]

    def update_place(self, place_id: int, data: dict):
        app.logger.debug(f"Update place {place_id} {data['name']}")
        self.json_client.put(f"/places/{place_id}", data=data)

    def upsert_place(self, data: dict) -> int:
        name = data["name"]
        app.logger.debug(f"Upsert place {name}")

        response = self.json_client.get(
            f"/organizations/{self.organization_id}/places?name={name}"
        )
        pagination = response.json()
        place = self._find_item_in_pagination(pagination, name)

        if not place:
            app.logger.debug(f"Place {name} does not exist")
            return self.insert_place(data)

        place_id = place["id"]
        app.logger.debug(f"Place {place_id} {name} already exists")
        self.update_place(place_id, data)
        return place_id

    def find_event_id_by_tag(self, tag: str) -> int:
        events = self.find_events_by_tag(tag)

        if len(events) != 1:
            return None

        event = events[0]
        return event["id"]

    def find_events_by_tag(self, tag: str) -> int:
        return self._find_events_by_tag_field("tag", tag)

    def find_events_by_internal_tag(self, tag: str) -> int:
        return self._find_events_by_tag_field("internal_tag", tag)

    def _find_events_by_tag_field(self, field: str, tag: str) -> int:
        events = list()
        page = 1

        while True:
            response = self.json_client.get(
                f"/organizations/{self.organization_id}/events/search?{field}={tag}&per_page=50&page={page}"
            )
            pagination = response.json()
            events.extend(pagination["items"])

            if pagination["has_next"]:
                page += 1
            else:
                break

        return events

    def insert_event(self, data: dict) -> int:
        app.logger.debug(f"Insert event {data['name']}")

        try:
            response = self.json_client.post(
                f"/organizations/{self.organization_id}/events", data=data
            )
        except UnprocessableEntityError as e:
            if e.json["errors"][0]["field"] == "photo":
                app.logger.warn("Retrying without photo")
                del data["photo"]
                response = self.json_client.post(
                    f"/organizations/{self.organization_id}/events", data=data
                )
            else:
                raise

        event = response.json()
        return event["id"]

    def update_event(self, event_id: int, data: dict):
        app.logger.debug(f"Update event {event_id}")

        try:
            self.json_client.put(f"/events/{event_id}", data=data)
        except UnprocessableEntityError as e:
            if e.json["errors"][0]["field"] == "photo":
                app.logger.warn("Retrying without photo")
                del data["photo"]
                self.json_client.put(f"/events/{event_id}", data=data)
            else:
                raise

    def patch_event(self, event_id: int, data: dict):
        app.logger.debug(f"Patch event {event_id}")

        try:
            self.json_client.patch(f"/events/{event_id}", data=data)
        except UnprocessableEntityError as e:
            if e.json["errors"][0]["field"] == "photo":
                app.logger.warn("Retrying without photo")
                del data["photo"]
                self.json_client.put(f"/events/{event_id}", data=data)
            else:
                raise

    def delete_event(self, event_id: int):
        app.logger.debug(f"Delete event {event_id}")

        try:
            self.json_client.delete(f"/events/{event_id}")
        except NotFoundError:
            app.logger.debug(f"Event {event_id} already deleted")

    def _find_item_in_pagination(self, pagination: dict, name: str) -> dict:
        for item in pagination["items"]:
            if item["name"] == name:
                return item

        return None
