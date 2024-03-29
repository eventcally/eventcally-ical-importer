"""empty message

Revision ID: 77b95441a7d7
Revises: d43954ccfb3b
Create Date: 2024-02-24 17:18:24.932732

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "77b95441a7d7"
down_revision = "d43954ccfb3b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "configuration",
        sa.Column(
            "categories",
            sa.UnicodeText(),
            server_default='{{ standard["categories"] }}',
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("configuration", "categories")
    # ### end Alembic commands ###
