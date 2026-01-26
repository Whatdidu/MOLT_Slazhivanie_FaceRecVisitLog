"""sync embeddings schema with model

Revision ID: 001_sync_embeddings
Revises: 270a2d558599
Create Date: 2026-01-26

Changes:
- Add vector_blob (LargeBinary) column
- Add vector_dim (Integer) column
- Migrate data from vector (ARRAY) to vector_blob (binary)
- Remove vector column
"""
from typing import Sequence, Union
import struct

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001_sync_embeddings'
down_revision: Union[str, Sequence[str], None] = '270a2d558599'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vector_blob and vector_dim columns, migrate data, remove vector column."""

    # 1. Add new columns
    op.add_column('embeddings', sa.Column('vector_blob', sa.LargeBinary(), nullable=True))
    op.add_column('embeddings', sa.Column('vector_dim', sa.Integer(), nullable=True, server_default='512'))

    # 2. Migrate data from vector (ARRAY) to vector_blob (binary)
    # Get connection for data migration
    connection = op.get_bind()

    # Fetch all existing embeddings with vector data
    result = connection.execute(sa.text("SELECT id, vector FROM embeddings WHERE vector IS NOT NULL"))
    rows = result.fetchall()

    for row in rows:
        embedding_id = row[0]
        vector_array = row[1]  # This is a Python list from PostgreSQL ARRAY

        if vector_array:
            # Convert float array to binary (same format as model uses)
            vector_blob = struct.pack(f'{len(vector_array)}f', *vector_array)
            vector_dim = len(vector_array)

            connection.execute(
                sa.text("UPDATE embeddings SET vector_blob = :blob, vector_dim = :dim WHERE id = :id"),
                {"blob": vector_blob, "dim": vector_dim, "id": embedding_id}
            )

    # 3. Make vector_blob NOT NULL (after data migration)
    op.alter_column('embeddings', 'vector_blob', nullable=False)
    op.alter_column('embeddings', 'vector_dim', nullable=False, server_default='512')

    # 4. Drop old vector column
    op.drop_column('embeddings', 'vector')


def downgrade() -> None:
    """Restore vector column, migrate data back, remove vector_blob and vector_dim."""

    # 1. Add vector column back
    op.add_column('embeddings', sa.Column('vector', postgresql.ARRAY(sa.Float()), nullable=True))

    # 2. Migrate data from vector_blob back to vector
    connection = op.get_bind()

    result = connection.execute(sa.text("SELECT id, vector_blob, vector_dim FROM embeddings WHERE vector_blob IS NOT NULL"))
    rows = result.fetchall()

    for row in rows:
        embedding_id = row[0]
        vector_blob = row[1]
        vector_dim = row[2]

        if vector_blob and vector_dim:
            # Convert binary back to float array
            vector_array = list(struct.unpack(f'{vector_dim}f', vector_blob))

            connection.execute(
                sa.text("UPDATE embeddings SET vector = :vec WHERE id = :id"),
                {"vec": vector_array, "id": embedding_id}
            )

    # 3. Make vector NOT NULL
    op.alter_column('embeddings', 'vector', nullable=False)

    # 4. Drop new columns
    op.drop_column('embeddings', 'vector_dim')
    op.drop_column('embeddings', 'vector_blob')
