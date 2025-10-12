"""Add VPS to service model

Revision ID: c6ac90386d54
Revises: d617fdfb66cd
Create Date: 2025-10-11 19:42:30.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6ac90386d54'
down_revision: Union[str, None] = 'd617fdfb66cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define old and new ENUM types
old_service_type = sa.Enum('MINECRAFT_PAPER', 'MINECRAFT_FORGE', 'MINECRAFT_VANILLA', 'PYTHON_BOT', 'NODEJS_APP', name='servicetype')
new_service_type = sa.Enum('MINECRAFT_PAPER', 'MINECRAFT_FORGE', 'MINECRAFT_VANILLA', 'PYTHON_BOT', 'NODEJS_APP', 'VPS', name='servicetype')


def upgrade() -> None:
    # Add the new column
    op.add_column('services', sa.Column('libvirt_domain_name', sa.String(), nullable=True))
    op.create_unique_constraint('uq_services_libvirt_domain_name', 'services', ['libvirt_domain_name'])

    # Alter the ENUM type
    op.execute('ALTER TYPE servicetype ADD VALUE \'VPS\'')


def downgrade() -> None:
    # Drop the column
    op.drop_constraint('uq_services_libvirt_domain_name', 'services', type_='unique')
    op.drop_column('services', 'libvirt_domain_name')

    # This is complex as removing a value from an ENUM is not straightforward.
    # The safest way is often to create a new table without the value, move data, and rename.
    # For this project, we will assume downgrading the ENUM is not a critical path and focus on upgrading.
    # A simple (but potentially failing) downgrade would be:
    op.execute("ALTER TYPE servicetype RENAME TO servicetype_old")
    new_service_type.create(op.get_bind())
    op.execute(
        "ALTER TABLE services ALTER COLUMN service_type TYPE servicetype USING service_type::text::servicetype"
    )
    op.execute("DROP TYPE servicetype_old")