"""stub - backend base migration (reference only)

This migration was created by the backend and already applied to the database.
It exists here so the microservice's migrations can reference it via depends_on.

Revision ID: 7468eec37172
Revises: None
Create Date: 2026-06-07 12:24:46.601065
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7468eec37172'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """This migration was already applied by the backend. No-op."""
    pass


def downgrade() -> None:
    """This migration was created by the backend. No-op."""
    pass
