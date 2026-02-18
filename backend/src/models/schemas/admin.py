import datetime

from src.models.schemas.base import BaseSchemaModel


class AdminActivityLogView(BaseSchemaModel):
    """Admin activity log view"""
    id: int
    admin_id: int | None
    admin_username: str | None = None
    action: str
    entity_type: str | None
    entity_id: int | None
    details: dict | None
    ip_address: str | None
    created_at: datetime.datetime


class AdminActivityLogListResponse(BaseSchemaModel):
    """Response for listing admin activity logs"""
    logs: list[AdminActivityLogView]
    total: int
    page: int
    page_size: int


class AdminDashboardStats(BaseSchemaModel):
    """Dashboard statistics for admin"""
    total_users: int
    active_users: int
    blocked_users: int
    admin_users: int
    new_users_today: int
    new_users_week: int
