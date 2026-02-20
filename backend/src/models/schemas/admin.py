# Admin schemas for activity logging and dashboard statistics
import datetime

from src.models.schemas.base import BaseSchemaModel


# Schema for viewing a single admin activity log entry
class AdminActivityLogView(BaseSchemaModel):
    """Admin activity log view"""
    id: int
    # ID of the admin who performed the action (None if system-generated)
    admin_id: int | None
    # Username of the admin for display purposes
    admin_username: str | None = None
    # Description of the action performed (e.g., "block_user", "create_event")
    action: str
    # Type of entity the action was performed on (e.g., "account", "event")
    entity_type: str | None
    # ID of the entity affected by the action
    entity_id: int | None
    # Additional context or metadata about the action (stored as JSON)
    details: dict | None
    # IP address from which the admin performed the action
    ip_address: str | None
    # When the action was performed
    created_at: datetime.datetime


# Paginated response for listing admin activity logs
class AdminActivityLogListResponse(BaseSchemaModel):
    """Response for listing admin activity logs"""
    # List of activity log entries for the current page
    logs: list[AdminActivityLogView]
    # Total number of matching log entries across all pages
    total: int
    # Current page number
    page: int
    # Number of entries per page
    page_size: int


# Schema for admin dashboard summary statistics about user accounts
class AdminDashboardStats(BaseSchemaModel):
    """Dashboard statistics for admin"""
    # Total number of registered user accounts
    total_users: int
    # Number of users who are not blocked
    active_users: int
    # Number of users who have been blocked by an admin
    blocked_users: int
    # Number of users with the admin role
    admin_users: int
    # Number of new user registrations today (UTC)
    new_users_today: int
    # Number of new user registrations in the last 7 days
    new_users_week: int
