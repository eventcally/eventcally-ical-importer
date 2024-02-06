import click
from flask.cli import AppGroup

from project import app

configuration_cli = AppGroup("configuration")


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


app.cli.add_command(configuration_cli)
