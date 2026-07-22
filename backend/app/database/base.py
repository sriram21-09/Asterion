# Import all ORM models here so that Base.metadata has them registered
# before running Alembic migrations.
from app.models.base import Base  # noqa: F401
from app.models.case import Case  # noqa: F401
from app.models.scenario import Scenario  # noqa: F401
from app.models.tower import Tower  # noqa: F401
from app.models.measurement import Measurement  # noqa: F401
from app.models.localization_result import LocalizationResult  # noqa: F401
from app.models.tracking_result import TrackingResult  # noqa: F401
from app.models.confidence_result import ConfidenceResult  # noqa: F401
from app.models.import_job import ImportJob  # noqa: F401
from app.models.cdr_record import CDRRecord  # noqa: F401

