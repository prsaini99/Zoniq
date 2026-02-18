"""
Admin Seat Management APIs
"""
from typing import Annotated

import fastapi
from fastapi import Query, Request

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import require_admin
from src.models.db.account import Account
from src.models.db.seat import SeatStatus
from src.models.schemas.event import (
    SeatCreate,
    SeatBulkCreate,
    SeatUpdate,
    SeatResponse,
)
from src.repository.crud.event import EventCRUDRepository
from src.repository.crud.seat_category import SeatCategoryCRUDRepository
from src.repository.crud.seat import SeatCRUDRepository
from src.services.admin_log_service import AdminLogService

router = fastapi.APIRouter(prefix="/seats", tags=["admin-seats"])


def _build_seat_response(seat) -> SeatResponse:
    """Build SeatResponse from Seat model"""
    return SeatResponse(
        id=seat.id,
        event_id=seat.event_id,
        category_id=seat.category_id,
        seat_number=seat.seat_number,
        row_name=seat.row_name,
        section=seat.section,
        status=seat.status,
        seat_label=seat.seat_label,
        position_x=seat.position_x,
        position_y=seat.position_y,
    )


# ==================== Seat Management ====================


@router.get(
    "/event/{event_id}",
    name="admin:seats:list",
    response_model=list[SeatResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_event_seats(
    event_id: int,
    category_id: int | None = None,
    status: str | None = None,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
) -> list[SeatResponse]:
    """Get all seats for an event (Admin only)"""
    seats = await seat_repo.read_seats_by_event(
        event_id=event_id,
        category_id=category_id,
        status=status,
        include_category=False,
    )

    return [_build_seat_response(seat) for seat in seats]


@router.get(
    "/event/{event_id}/counts",
    name="admin:seats:counts",
    response_model=dict,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_seat_counts(
    event_id: int,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
) -> dict:
    """Get seat counts by status for an event"""
    return await seat_repo.get_seat_counts_by_event(event_id=event_id)


@router.post(
    "/event/{event_id}",
    name="admin:seats:create",
    response_model=SeatResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_seat(
    event_id: int,
    seat_create: SeatCreate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatResponse:
    """Create a single seat for an event"""
    seat = await seat_repo.create_seat(event_id=event_id, seat_create=seat_create)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="create_seat",
        entity_type="seat",
        entity_id=seat.id,
        details={"event_id": event_id, "seat_label": seat.seat_label},
        ip_address=request.client.host if request.client else None,
    )

    return _build_seat_response(seat)


@router.post(
    "/event/{event_id}/bulk",
    name="admin:seats:bulk-create",
    response_model=dict,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def bulk_create_seats(
    event_id: int,
    bulk_create: SeatBulkCreate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> dict:
    """
    Bulk create seats for an event.

    Example: Create seats A1-A10, B1-B10, C1-C10
    ```json
    {
        "category_id": 1,
        "section": "Floor",
        "rows": ["A", "B", "C"],
        "seats_per_row": 10
    }
    ```
    """
    seats = await seat_repo.bulk_create_seats(event_id=event_id, bulk_create=bulk_create)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="bulk_create_seats",
        entity_type="seat",
        entity_id=event_id,
        details={
            "event_id": event_id,
            "rows": bulk_create.rows,
            "seats_per_row": bulk_create.seats_per_row,
            "total_created": len(seats),
        },
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": f"Created {len(seats)} seats successfully",
        "seats_created": len(seats),
    }


@router.get(
    "/{seat_id}",
    name="admin:seats:get",
    response_model=SeatResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_seat(
    seat_id: int,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
) -> SeatResponse:
    """Get seat details by ID"""
    seat = await seat_repo.read_seat_by_id(seat_id=seat_id)
    return _build_seat_response(seat)


@router.patch(
    "/{seat_id}",
    name="admin:seats:update",
    response_model=SeatResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_seat(
    seat_id: int,
    seat_update: SeatUpdate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatResponse:
    """Update a seat"""
    seat = await seat_repo.update_seat(seat_id=seat_id, seat_update=seat_update)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="update_seat",
        entity_type="seat",
        entity_id=seat.id,
        details={"updates": seat_update.model_dump(exclude_unset=True)},
        ip_address=request.client.host if request.client else None,
    )

    return _build_seat_response(seat)


@router.post(
    "/{seat_id}/block",
    name="admin:seats:block",
    response_model=SeatResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def block_seat(
    seat_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatResponse:
    """Block a seat (not for sale)"""
    seat = await seat_repo.block_seat(seat_id=seat_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="block_seat",
        entity_type="seat",
        entity_id=seat.id,
        details={"seat_label": seat.seat_label},
        ip_address=request.client.host if request.client else None,
    )

    return _build_seat_response(seat)


@router.post(
    "/{seat_id}/unblock",
    name="admin:seats:unblock",
    response_model=SeatResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def unblock_seat(
    seat_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatResponse:
    """Unblock a seat (make available for sale)"""
    seat = await seat_repo.unblock_seat(seat_id=seat_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="unblock_seat",
        entity_type="seat",
        entity_id=seat.id,
        details={"seat_label": seat.seat_label},
        ip_address=request.client.host if request.client else None,
    )

    return _build_seat_response(seat)


@router.post(
    "/{seat_id}/release",
    name="admin:seats:release",
    response_model=SeatResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def force_release_seat(
    seat_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatResponse:
    """Force release a locked seat (admin override)"""
    await seat_repo.unlock_seats(seat_ids=[seat_id])
    seat = await seat_repo.read_seat_by_id(seat_id=seat_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="force_release_seat",
        entity_type="seat",
        entity_id=seat.id,
        details={"seat_label": seat.seat_label},
        ip_address=request.client.host if request.client else None,
    )

    return _build_seat_response(seat)


@router.delete(
    "/{seat_id}",
    name="admin:seats:delete",
    status_code=fastapi.status.HTTP_200_OK,
)
async def delete_seat(
    seat_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> dict:
    """Delete a seat (only if available or blocked)"""
    # Get seat first for logging
    seat = await seat_repo.read_seat_by_id(seat_id=seat_id)
    seat_label = seat.seat_label
    event_id = seat.event_id

    await seat_repo.delete_seat(seat_id=seat_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="delete_seat",
        entity_type="seat",
        entity_id=seat_id,
        details={"event_id": event_id, "seat_label": seat_label},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Seat '{seat_label}' deleted successfully"}


@router.post(
    "/release-expired",
    name="admin:seats:release-expired",
    status_code=fastapi.status.HTTP_200_OK,
)
async def release_expired_locks(
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> dict:
    """Release all expired seat locks (maintenance task)"""
    released_count = await seat_repo.release_expired_locks()

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="release_expired_locks",
        entity_type="seat",
        entity_id=None,
        details={"released_count": released_count},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": f"Released {released_count} expired seat locks",
        "released_count": released_count,
    }
