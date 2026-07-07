# Import all ORM models here so that Base.metadata has them registered
# before running Alembic migrations.
from app.models.base import Base
from app.models.case import Case
from app.models.scenario import Scenario
