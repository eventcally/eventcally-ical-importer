"""empty message

Revision ID: e9a8d9dedfe0
Revises: edbe32b50a0a
Create Date: 2024-02-13 15:11:38.448654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9a8d9dedfe0'
down_revision = 'edbe32b50a0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('configuration', sa.Column('identifier_tag', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('configuration', 'identifier_tag')
    # ### end Alembic commands ###