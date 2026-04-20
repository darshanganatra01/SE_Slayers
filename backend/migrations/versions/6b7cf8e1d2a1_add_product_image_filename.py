"""Add product image filename

Revision ID: 6b7cf8e1d2a1
Revises: a50309bf61c3, 786a25bf4c12
Create Date: 2026-04-20 02:05:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6b7cf8e1d2a1"
down_revision = ("a50309bf61c3", "786a25bf4c12")
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image_filename", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("image_filename")
