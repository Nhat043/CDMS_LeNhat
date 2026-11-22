"""drop the unused sequence on product_state

Revision ID: 2e63b3f0e9dd
Revises: 79afd9160833
Create Date: 2026-11-22 19:38:03.820944

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2e63b3f0e9dd"
down_revision: Union[str, Sequence[str], None] = "79afd9160833"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("product_state", "product_id", server_default=None)
    op.execute("DROP SEQUENCE IF EXISTS product_state_product_id_seq")


def downgrade() -> None:
    op.execute(
        "CREATE SEQUENCE product_state_product_id_seq OWNED BY product_state.product_id"
    )
    op.alter_column(
        "product_state",
        "product_id",
        server_default=sa.text("nextval('product_state_product_id_seq')"),
    )
