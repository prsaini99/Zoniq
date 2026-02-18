"""
Admin Venue Management APIs
"""
from typing import Annotated

import fastapi
from fastapi import Query, Request

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import require_admin
from src.models.db.account import Account
from src.models.schemas.venue import (
    VenueCreate,
    VenueUpdate,
    VenueResponse,
    VenueDetailResponse,
    VenueListResponse,
)
from src.repository.crud.venue import VenueCRUDRepository
from src.services.admin_log_service import AdminLogService

router = fastapi.APIRouter(prefix="/venues", tags=["admin-venues"])


def _build_venue_response(venue) -> VenueResponse:
    """Build VenueResponse from Venue model"""
    return VenueResponse(
        id=venue.id,
        name=venue.name,
        address=venue.address,
        city=venue.city,
        state=venue.state,
        country=venue.country,
        pincode=venue.pincode,
        capacity=venue.capacity,
        contact_phone=venue.contact_phone,
        contact_email=venue.contact_email,
        is_active=venue.is_active,
        created_at=venue.created_at,
        updated_at=venue.updated_at,
    )


def _build_venue_detail_response(venue) -> VenueDetailResponse:
    """Build VenueDetailResponse from Venue model"""
    return VenueDetailResponse(
        id=venue.id,
        name=venue.name,
        address=venue.address,
        city=venue.city,
        state=venue.state,
        country=venue.country,
        pincode=venue.pincode,
        capacity=venue.capacity,
        seat_map_config=venue.seat_map_config,
        contact_phone=venue.contact_phone,
        contact_email=venue.contact_email,
        is_active=venue.is_active,
        created_at=venue.created_at,
        updated_at=venue.updated_at,
    )


@router.get(
    "",
    name="admin:venues:list",
    response_model=VenueListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_venues(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    city: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    admin: Account = fastapi.Depends(require_admin),
    venue_repo: VenueCRUDRepository = fastapi.Depends(
        get_repository(repo_type=VenueCRUDRepository)
    ),
) -> VenueListResponse:
    """List all venues with optional filters (Admin only)"""
    venues, total = await venue_repo.read_venues(
        page=page,
        page_size=page_size,
        city=city,
        is_active=is_active,
        search=search,
    )

    return VenueListResponse(
        venues=[_build_venue_response(venue) for venue in venues],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/all",
    name="admin:venues:all",
    response_model=list[VenueResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_all_active_venues(
    admin: Account = fastapi.Depends(require_admin),
    venue_repo: VenueCRUDRepository = fastapi.Depends(
        get_repository(repo_type=VenueCRUDRepository)
    ),
) -> list[VenueResponse]:
    """Get all active venues (for dropdowns)"""
    venues = await venue_repo.read_all_active_venues()
    return [_build_venue_response(venue) for venue in venues]


@router.post(
    "",
    name="admin:venues:create",
    response_model=VenueDetailResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_venue(
    venue_create: VenueCreate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    venue_repo: VenueCRUDRepository = fastapi.Depends(
        get_repository(repo_type=VenueCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> VenueDetailResponse:
    """Create a new venue (Admin only)"""
    venue = await venue_repo.create_venue(venue_create=venue_create)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="create_venue",
        entity_type="venue",
        entity_id=venue.id,
        details={"venue_name": venue.name},
        ip_address=request.client.host if request.client else None,
    )

    return _build_venue_detail_response(venue)


@router.get(
    "/{venue_id}",
    name="admin:venues:get",
    response_model=VenueDetailResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_venue(
    venue_id: int,
    admin: Account = fastapi.Depends(require_admin),
    venue_repo: VenueCRUDRepository = fastapi.Depends(
        get_repository(repo_type=VenueCRUDRepository)
    ),
) -> VenueDetailResponse:
    """Get venue details by ID (Admin only)"""
    venue = await venue_repo.read_venue_by_id(venue_id=venue_id)
    return _build_venue_detail_response(venue)


@router.patch(
    "/{venue_id}",
    name="admin:venues:update",
    response_model=VenueDetailResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_venue(
    venue_id: int,
    venue_update: VenueUpdate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    venue_repo: VenueCRUDRepository = fastapi.Depends(
        get_repository(repo_type=VenueCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> VenueDetailResponse:
    """Update a venue (Admin only)"""
    venue = await venue_repo.update_venue(venue_id=venue_id, venue_update=venue_update)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="update_venue",
        entity_type="venue",
        entity_id=venue.id,
        details={"updates": venue_update.model_dump(exclude_unset=True)},
        ip_address=request.client.host if request.client else None,
    )

    return _build_venue_detail_response(venue)


@router.delete(
    "/{venue_id}",
    name="admin:venues:delete",
    status_code=fastapi.status.HTTP_200_OK,
)
async def delete_venue(
    venue_id: int,
    request: Request,
    permanent: bool = False,
    admin: Account = fastapi.Depends(require_admin),
    venue_repo: VenueCRUDRepository = fastapi.Depends(
        get_repository(repo_type=VenueCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> dict:
    """
    Delete a venue (Admin only).

    By default, performs a soft delete (sets is_active=False).
    Set permanent=True to permanently delete.
    """
    # Get venue first for logging
    venue = await venue_repo.read_venue_by_id(venue_id=venue_id)
    venue_name = venue.name

    if permanent:
        await venue_repo.hard_delete_venue(venue_id=venue_id)
        action = "hard_delete_venue"
        message = f"Venue '{venue_name}' permanently deleted"
    else:
        await venue_repo.delete_venue(venue_id=venue_id)
        action = "soft_delete_venue"
        message = f"Venue '{venue_name}' deactivated"

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action=action,
        entity_type="venue",
        entity_id=venue_id,
        details={"venue_name": venue_name, "permanent": permanent},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": message}
