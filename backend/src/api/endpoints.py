import fastapi

from src.api.routes.account import router as account_router
from src.api.routes.authentication import router as auth_router
from src.api.routes.users import router as users_router
from src.api.routes.events import router as events_router
from src.api.routes.cart import router as cart_router
from src.api.routes.bookings import router as bookings_router
from src.api.routes.payments import router as payments_router
from src.api.routes.tickets import router as tickets_router
from src.api.routes.notifications import router as notifications_router
from src.api.routes.queue import router as queue_router
from src.api.routes.websocket import router as websocket_router
from src.api.routes.wishlist import router as wishlist_router
from src.api.routes.admin.users import router as admin_users_router
from src.api.routes.admin.logs import router as admin_logs_router
from src.api.routes.admin.venues import router as admin_venues_router
from src.api.routes.admin.events import router as admin_events_router
from src.api.routes.admin.seats import router as admin_seats_router
from src.api.routes.admin.bookings import router as admin_bookings_router
from src.api.routes.admin.dashboard import router as admin_dashboard_router

router = fastapi.APIRouter()

# Public routes
router.include_router(router=account_router)
router.include_router(router=auth_router)
router.include_router(router=events_router)

# User routes (authenticated)
router.include_router(router=users_router)
router.include_router(router=cart_router)
router.include_router(router=bookings_router)
router.include_router(router=payments_router)
router.include_router(router=tickets_router)
router.include_router(router=notifications_router)
router.include_router(router=queue_router)
router.include_router(router=wishlist_router)

# WebSocket routes
router.include_router(router=websocket_router)

# Admin routes
router.include_router(router=admin_users_router, prefix="/admin")
router.include_router(router=admin_logs_router, prefix="/admin")
router.include_router(router=admin_venues_router, prefix="/admin")
router.include_router(router=admin_events_router, prefix="/admin")
router.include_router(router=admin_seats_router, prefix="/admin")
router.include_router(router=admin_bookings_router, prefix="/admin")
router.include_router(router=admin_dashboard_router, prefix="/admin")
