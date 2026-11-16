import json

import click
from flask.cli import AppGroup

from project import app

configuration_cli = AppGroup("configuration")
bff_cli = AppGroup("bff")


@configuration_cli.command("run")
@click.argument("id", type=int)
def configuration_run(id: int):
    from project import db
    from project.ical_importer import IcalImporter
    from project.models import Configuration

    configuration = Configuration.query.get(id)

    importer = IcalImporter()
    importer.dry = False
    importer.perform(configuration)

    db.session.commit()


@bff_cli.command("openapi")
def bff_openapi():
    """Print the OpenAPI document of the BFF (the source of frontend/openapi.json)."""
    from project.bff.openapi import build_openapi

    click.echo(json.dumps(build_openapi(), indent=2, sort_keys=True))


app.cli.add_command(configuration_cli)
app.cli.add_command(bff_cli)
