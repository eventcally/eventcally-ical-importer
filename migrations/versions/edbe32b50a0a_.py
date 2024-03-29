"""empty message

Revision ID: edbe32b50a0a
Revises:
Create Date: 2024-02-08 16:56:51.489324

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "edbe32b50a0a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=255), nullable=True),
        sa.Column("token_type", sa.String(length=255), nullable=True),
        sa.Column("access_token", sa.String(length=255), nullable=True),
        sa.Column("refresh_token", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
        sa.UniqueConstraint("email", name=op.f("uq_user_email")),
    )
    op.create_table(
        "configuration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Unicode(length=255), nullable=True),
        sa.Column("url", sa.Unicode(length=255), nullable=True),
        sa.Column("organization_id", sa.Unicode(length=255), nullable=True),
        sa.Column(
            "name",
            sa.UnicodeText(),
            server_default='{{ standard["name"] }}',
            nullable=True,
        ),
        sa.Column(
            "organizer_name",
            sa.UnicodeText(),
            server_default='{{ standard["organizer_name"] }}',
            nullable=True,
        ),
        sa.Column(
            "place_name",
            sa.UnicodeText(),
            server_default='{{ standard["place_name"] }}',
            nullable=True,
        ),
        sa.Column(
            "start",
            sa.UnicodeText(),
            server_default='{{ standard["start"] }}',
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.UnicodeText(),
            server_default='{{ standard["description"] }}',
            nullable=True,
        ),
        sa.Column(
            "end",
            sa.UnicodeText(),
            server_default='{{ standard["end"] }}',
            nullable=True,
        ),
        sa.Column(
            "allday",
            sa.UnicodeText(),
            server_default='{{ standard["allday"] }}',
            nullable=True,
        ),
        sa.Column(
            "external_link",
            sa.UnicodeText(),
            server_default='{{ standard["external_link"] }}',
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_configuration_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_configuration")),
    )
    op.create_table(
        "importedevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("configuration_id", sa.Integer(), nullable=False),
        sa.Column("vevent_uid", sa.Unicode(length=255), nullable=True),
        sa.Column("eventcally_event_id", sa.Unicode(length=255), nullable=True),
        sa.Column("event", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["configuration_id"],
            ["configuration.id"],
            name=op.f("fk_importedevent_configuration_id_configuration"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_importedevent")),
    )
    op.create_table(
        "run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("configuration_id", sa.Integer(), nullable=False),
        sa.Column(
            "configuration_settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=255), nullable=True),
        sa.Column("failure_event_count", sa.Integer(), nullable=True),
        sa.Column("skipped_event_count", sa.Integer(), nullable=True),
        sa.Column("new_event_count", sa.Integer(), nullable=True),
        sa.Column("updated_event_count", sa.Integer(), nullable=True),
        sa.Column("unchanged_event_count", sa.Integer(), nullable=True),
        sa.Column("deleted_event_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["configuration_id"],
            ["configuration.id"],
            name=op.f("fk_run_configuration_id_configuration"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run")),
    )
    op.create_table(
        "logentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("message", sa.UnicodeText(), nullable=True),
        sa.Column("type", sa.String(length=255), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"], ["run.id"], name=op.f("fk_logentry_run_id_run")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_logentry")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("logentry")
    op.drop_table("run")
    op.drop_table("importedevent")
    op.drop_table("configuration")
    op.drop_table("user")
    # ### end Alembic commands ###
