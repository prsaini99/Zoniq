"""Phase 1: User management and admin setup

Revision ID: phase1_user_mgmt
Revises: 60d1844cb5d3
Create Date: 2024-01-01 00:01:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "phase1_user_mgmt"
down_revision = "60d1844cb5d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to account table
    op.add_column("account", sa.Column("role", sa.String(length=20), nullable=False, server_default="user"))
    op.add_column("account", sa.Column("phone", sa.String(length=20), nullable=True))
    op.add_column("account", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("account", sa.Column("is_phone_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("account", sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("account", sa.Column("blocked_reason", sa.Text(), nullable=True))
    op.add_column("account", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    # Create OTP codes table
    op.create_table(
        "otp_code",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_code_phone", "otp_code", ["phone"], unique=False)
    op.create_index("ix_otp_code_email", "otp_code", ["email"], unique=False)
    op.create_index("ix_otp_code_purpose", "otp_code", ["purpose"], unique=False)

    # Create user devices table
    op.create_table(
        "user_device",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_fingerprint", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("browser", sa.String(length=100), nullable=True),
        sa.Column("os", sa.String(length=100), nullable=True),
        sa.Column("is_trusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_device_user_id", "user_device", ["user_id"], unique=False)

    # Create admin activity log table
    op.create_table(
        "admin_activity_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["account.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_activity_log_admin_id", "admin_activity_log", ["admin_id"], unique=False)
    op.create_index("ix_admin_activity_log_created_at", "admin_activity_log", ["created_at"], unique=False)
    op.create_index("ix_admin_activity_log_entity", "admin_activity_log", ["entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    # Drop admin activity log table
    op.drop_index("ix_admin_activity_log_entity", table_name="admin_activity_log")
    op.drop_index("ix_admin_activity_log_created_at", table_name="admin_activity_log")
    op.drop_index("ix_admin_activity_log_admin_id", table_name="admin_activity_log")
    op.drop_table("admin_activity_log")

    # Drop user devices table
    op.drop_index("ix_user_device_user_id", table_name="user_device")
    op.drop_table("user_device")

    # Drop OTP codes table
    op.drop_index("ix_otp_code_purpose", table_name="otp_code")
    op.drop_index("ix_otp_code_email", table_name="otp_code")
    op.drop_index("ix_otp_code_phone", table_name="otp_code")
    op.drop_table("otp_code")

    # Remove new columns from account table
    op.drop_column("account", "last_login_at")
    op.drop_column("account", "blocked_reason")
    op.drop_column("account", "is_blocked")
    op.drop_column("account", "is_phone_verified")
    op.drop_column("account", "full_name")
    op.drop_column("account", "phone")
    op.drop_column("account", "role")
