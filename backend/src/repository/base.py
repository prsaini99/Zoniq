# Model registration module -- imports all ORM models so that SQLAlchemy's Base.metadata
# is aware of every table before create_all() or Alembic migrations run.
# Without these imports, tables would not be registered in the metadata.

from src.models.db.account import Account
from src.models.db.otp import OTPCode
from src.models.db.user_device import UserDevice
from src.models.db.admin_activity_log import AdminActivityLog
from src.models.db.venue import Venue
from src.models.db.event import Event
from src.models.db.seat_category import SeatCategory
from src.models.db.seat import Seat
from src.models.db.booking import Booking, BookingItem
from src.models.db.cart import Cart, CartItem
from src.models.db.payment import Payment
from src.models.db.ticket_transfer import TicketTransfer
from src.models.db.notification_preference import NotificationPreference
from src.models.db.queue_entry import QueueEntry
from src.models.db.wishlist import Wishlist
from src.repository.table import Base
