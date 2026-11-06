"""initial_schema

Revision ID: 09d1c0b980a5
Revises: 
Create Date: 2026-11-06 08:25:45.973301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "09d1c0b980a5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=120), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    if "medications" not in existing_tables:
        op.create_table(
            "medications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("presentation", sa.String(length=80), nullable=False),
            sa.Column("stock", sa.Integer(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_medications_id"), "medications", ["id"], unique=False)
        op.create_index(op.f("ix_medications_owner_id"), "medications", ["owner_id"], unique=False)

    if "treatments" not in existing_tables:
        op.create_table(
            "treatments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("medication_id", sa.Integer(), nullable=False),
            sa.Column("dosage", sa.String(length=80), nullable=False),
            sa.Column("schedule_times", sa.Text(), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("duration_days", sa.Integer(), nullable=False),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_treatments_id"), "treatments", ["id"], unique=False)
        op.create_index(op.f("ix_treatments_medication_id"), "treatments", ["medication_id"], unique=False)
        op.create_index(op.f("ix_treatments_owner_id"), "treatments", ["owner_id"], unique=False)

    if "doses" not in existing_tables:
        op.create_table(
            "doses",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("treatment_id", sa.Integer(), nullable=False),
            sa.Column("scheduled_at", sa.DateTime(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("decided_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["treatment_id"], ["treatments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_doses_id"), "doses", ["id"], unique=False)
        op.create_index(op.f("ix_doses_scheduled_at"), "doses", ["scheduled_at"], unique=False)
        op.create_index(op.f("ix_doses_treatment_id"), "doses", ["treatment_id"], unique=False)
        op.create_index(op.f("ix_doses_user_id"), "doses", ["user_id"], unique=False)
    else:
        with op.batch_alter_table("doses", schema=None) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DATETIME(),
                nullable=False,
            )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("doses")
    op.drop_table("treatments")
    op.drop_table("medications")
    op.drop_table("users")
