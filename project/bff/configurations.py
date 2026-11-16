from project.bff import bff_bp
from project.bff.routing import bff_route
from project.bff.schemas import (
    AppInstallationItem,
    ConfigurationCreate,
    ConfigurationCreated,
    ConfigurationDetail,
    ConfigurationForm,
    ConfigurationFormRead,
    ConfigurationList,
    ConfigurationListItem,
    ImportedEventItem,
    RunListItem,
)

FORM_FIELDS = ["title", "identifier_tag", "url"]


def get_configurations_query():
    """The configurations of the organizations the current user administrates."""
    from project import current_user
    from project.models import AppInstallation, Configuration, User

    return Configuration.query.join(
        AppInstallation, AppInstallation.id == Configuration.app_installation_id
    ).filter(AppInstallation.users.any(User.id == current_user.id))


def get_configuration_or_404(id: int):
    from project.models import Configuration

    return get_configurations_query().filter(Configuration.id == id).first_or_404()


def apply_form(configuration, body: ConfigurationForm):
    for key, value in body.model_dump().items():
        setattr(configuration, key, value)


@bff_route(
    bff_bp,
    "/configurations",
    response=ConfigurationList,
    summary="The user's configurations and the organizations they can create one for",
)
def configuration_list():
    from project import current_user

    return ConfigurationList(
        configurations=[
            ConfigurationListItem(
                id=c.id,
                title=c.title,
                organization_name=c.app_installation.organization_name,
            )
            for c in get_configurations_query().all()
        ],
        app_installations=[
            AppInstallationItem(id=i.id, organization_name=i.organization_name)
            for i in current_user.app_installations
        ],
    )


@bff_route(
    bff_bp,
    "/configurations",
    method="POST",
    body=ConfigurationCreate,
    response=ConfigurationCreated,
    status=201,
    summary="Create an empty configuration for one of the user's organizations",
)
def configuration_create(body: ConfigurationCreate):
    from project import current_user, db
    from project.models import Configuration, UserAppInstallations

    UserAppInstallations.query.filter(
        UserAppInstallations.app_installation_id == body.app_installation_id
    ).filter(UserAppInstallations.user_id == current_user.id).first_or_404()

    configuration = Configuration()
    configuration.app_installation_id = body.app_installation_id

    db.session.add(configuration)
    db.session.commit()

    return ConfigurationCreated(id=configuration.id)


@bff_route(bff_bp, "/configurations/<int:id>", response=ConfigurationDetail)
def configuration_read(id: int):
    configuration = get_configuration_or_404(id)

    return ConfigurationDetail(
        id=configuration.id,
        title=configuration.title,
        url=configuration.url,
        organization_name=configuration.app_installation.organization_name,
        runs=[
            RunListItem.model_validate(run, from_attributes=True)
            for run in configuration.runs
        ],
        imported_events=[
            ImportedEventItem(
                id=imported_event.id,
                vevent_uid=imported_event.vevent_uid,
                eventcally_event_id=imported_event.eventcally_event_id,
                eventcally_url=imported_event.get_eventcally_url(),
                event=imported_event.event,
            )
            for imported_event in configuration.imported_events
        ],
    )


@bff_route(bff_bp, "/configurations/<int:id>/form", response=ConfigurationFormRead)
def configuration_form(id: int):
    from project.models import Configuration

    configuration = get_configuration_or_404(id)
    fields = FORM_FIELDS + Configuration._mapper_attrs

    return ConfigurationFormRead(
        id=configuration.id,
        organization_name=configuration.app_installation.organization_name,
        # Not validated: an old configuration may hold values the form refuses on save.
        values=ConfigurationForm.model_construct(
            **{key: getattr(configuration, key) for key in fields}
        ),
        mapper_fields=Configuration._mapper_attrs,
    )


@bff_route(bff_bp, "/configurations/<int:id>", method="PUT", body=ConfigurationForm)
def configuration_update(id: int, body: ConfigurationForm):
    from project import db

    configuration = get_configuration_or_404(id)
    apply_form(configuration, body)
    db.session.commit()


@bff_route(bff_bp, "/configurations/<int:id>/delete", method="POST")
def configuration_delete(id: int):
    from project import db

    configuration = get_configuration_or_404(id)
    db.session.delete(configuration)
    db.session.commit()
