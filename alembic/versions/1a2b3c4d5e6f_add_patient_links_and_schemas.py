"""add_patient_links_and_schemas

Revision ID: 1a2b3c4d5e6f
Revises: 09d1c0b980a5
Create Date: 2026-11-11 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "09d1c0b980a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega tablas de enlaces paciente-gestor, esquemas y ajusta longitud de users.role."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" in existing_tables:
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column(
                "role",
                existing_type=sa.String(length=20),
                type_=sa.String(length=30),
                existing_nullable=False,
            )

    if "patient_links" not in existing_tables:
        op.create_table(
            "patient_links",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("manager_id", sa.Integer(), nullable=False),
            sa.Column("patient_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("responded_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_patient_links_id"), "patient_links", ["id"], unique=False)
        op.create_index(op.f("ix_patient_links_manager_id"), "patient_links", ["manager_id"], unique=False)
        op.create_index(op.f("ix_patient_links_patient_id"), "patient_links", ["patient_id"], unique=False)

    if "medication_schemas" not in existing_tables:
        op.create_table(
            "medication_schemas",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("manager_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("medication_name", sa.String(length=120), nullable=False),
            sa.Column("presentation", sa.String(length=80), nullable=False),
            sa.Column("default_stock", sa.Integer(), nullable=False),
            sa.Column("dosage", sa.String(length=80), nullable=False),
            sa.Column("schedule_times", sa.Text(), nullable=False),
            sa.Column("duration_days", sa.Integer(), nullable=False),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_medication_schemas_id"), "medication_schemas", ["id"], unique=False)
        op.create_index(op.f("ix_medication_schemas_manager_id"), "medication_schemas", ["manager_id"], unique=False)


def downgrade() -> None:
    """Revierte las tablas de enlaces y esquemas."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "medication_schemas" in existing_tables:
        op.drop_table("medication_schemas")
    if "patient_links" in existing_tables:
        op.drop_table("patient_links")
    if "users" in existing_tables:
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column(
                "role",
                existing_type=sa.String(length=30),
                type_=sa.String(length=20),
                existing_nullable=False,
            )
