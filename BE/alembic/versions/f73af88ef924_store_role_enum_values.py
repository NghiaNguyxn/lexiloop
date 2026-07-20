"""store role enum values

Revision ID: f73af88ef924
Revises: bcbdd0bd3f0b
Create Date: 2026-07-20 09:47:37.195853

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f73af88ef924'
down_revision: Union[str, Sequence[str], None] = 'bcbdd0bd3f0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        "ALTER TYPE role RENAME VALUE 'USER' TO 'user'"
    )
    op.execute(
        "ALTER TYPE role RENAME VALUE 'ADMIN' TO 'admin'"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        "ALTER TYPE role RENAME VALUE 'user' TO 'USER'"
    )
    op.execute(
        "ALTER TYPE role RENAME VALUE 'admin' TO 'ADMIN'"
    )
