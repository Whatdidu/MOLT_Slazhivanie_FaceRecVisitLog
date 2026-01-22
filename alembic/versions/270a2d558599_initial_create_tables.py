"""initial_create_tables

Revision ID: 270a2d558599
Revises:
Create Date: 2026-01-22 18:34:17.667805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '270a2d558599'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='Primary key'),
        sa.Column('full_name', sa.String(255), nullable=False, comment='Full name of the employee'),
        sa.Column('email', sa.String(255), nullable=False, unique=True, comment='Unique email address'),
        sa.Column('department', sa.String(100), nullable=True, comment='Department name'),
        sa.Column('photo_path', sa.String(500), nullable=True, comment='Path to employee photo (temporary)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Whether the employee is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Record creation timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment='Record last update timestamp (UTC)'),
    )
    op.create_index('ix_employees_id', 'employees', ['id'])
    op.create_index('ix_employees_email', 'employees', ['email'])

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='Primary key'),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to Employee'),
        sa.Column('vector', sa.ARRAY(sa.Float()), nullable=False, comment='Face embedding vector'),
        sa.Column('model_version', sa.String(50), nullable=False, default='arcface', comment='ML model version used'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Record creation timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment='Record last update timestamp (UTC)'),
    )
    op.create_index('ix_embeddings_id', 'embeddings', ['id'])
    op.create_index('ix_embeddings_employee_id', 'embeddings', ['employee_id'])

    # Create attendance_log table
    op.create_table(
        'attendance_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='Primary key'),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True, comment='Foreign key to Employee (null for unknown faces)'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Event timestamp (UTC)'),
        sa.Column('event_type', sa.String(20), nullable=False, default='entry', comment='Event type (entry/exit)'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Recognition confidence score (0-1)'),
        sa.Column('trace_id', sa.String(36), nullable=False, comment='Unique trace ID for request tracking (UUID)'),
        sa.Column('photo_path', sa.String(500), nullable=True, comment='Path to snapshot photo (TTL 7 days)'),
        sa.Column('status', sa.String(20), nullable=False, default='unknown', comment='Recognition status (match/unknown/low_confidence/no_face/error)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='Record creation timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(), comment='Record last update timestamp (UTC)'),
    )
    op.create_index('ix_attendance_log_id', 'attendance_log', ['id'])
    op.create_index('ix_attendance_log_employee_id', 'attendance_log', ['employee_id'])
    op.create_index('ix_attendance_log_timestamp', 'attendance_log', ['timestamp'])
    op.create_index('ix_attendance_log_trace_id', 'attendance_log', ['trace_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('ix_attendance_log_trace_id', 'attendance_log')
    op.drop_index('ix_attendance_log_timestamp', 'attendance_log')
    op.drop_index('ix_attendance_log_employee_id', 'attendance_log')
    op.drop_index('ix_attendance_log_id', 'attendance_log')
    op.drop_table('attendance_log')

    op.drop_index('ix_embeddings_employee_id', 'embeddings')
    op.drop_index('ix_embeddings_id', 'embeddings')
    op.drop_table('embeddings')

    op.drop_index('ix_employees_email', 'employees')
    op.drop_index('ix_employees_id', 'employees')
    op.drop_table('employees')
