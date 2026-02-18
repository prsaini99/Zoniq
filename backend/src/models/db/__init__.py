# Import all models so SQLAlchemy relationships resolve correctly
from src.models.db.account import Account  # noqa: F401
from src.models.db.event import Event  # noqa: F401
from src.models.db.venue import Venue  # noqa: F401
from src.models.db.seat_category import SeatCategory  # noqa: F401
from src.models.db.seat import Seat  # noqa: F401
from src.models.db.booking import Booking  # noqa: F401
from src.models.db.cart import Cart  # noqa: F401
from src.models.db.payment import Payment  # noqa: F401
from src.models.db.wishlist import Wishlist  # noqa: F401
from src.models.db.queue_entry import QueueEntry  # noqa: F401
from src.models.db.otp import OTP  # noqa: F401
from src.models.db.ticket_transfer import TicketTransfer  # noqa: F401
from src.models.db.notification_preference import NotificationPreference  # noqa: F401
from src.models.db.user_device import UserDevice  # noqa: F401
from src.models.db.admin_activity_log import AdminActivityLog  # noqa: F401
