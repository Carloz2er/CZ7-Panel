# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.session import Base
from app.models.user import User
from app.models.ticket import Ticket, TicketMessage
from app.models.announcement import Announcement
from app.models.service import Service
from app.models.backup import Backup
from app.models.subscription import Plan, Subscription