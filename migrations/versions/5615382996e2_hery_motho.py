"""hery motho

Revision ID: 5615382996e2
Revises: c5fca89b8350
Create Date: 2024-10-23 15:49:01.918202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5615382996e2'
down_revision = 'c5fca89b8350'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.drop_column('pdf_file')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('photo')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photo', sa.VARCHAR(length=200), nullable=True))

    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pdf_file', sa.VARCHAR(length=200), nullable=True))

    # ### end Alembic commands ###
