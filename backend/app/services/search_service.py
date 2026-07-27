"""Global Search service querying across CDR records, towers, and cases.

All queries use SQLAlchemy ORM ilike() — parameterized SQL, SQL-injection safe.
"""

from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.tower import Tower
from app.schemas.search import (
    CaseSearchResult,
    CDRSearchResult,
    PaginatedSearchResponse,
    TowerSearchResult,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session


class SearchService:
    """Unified search across CDR records, towers, and cases.

    # ponytail: static class — no instantiation needed
    """

    @staticmethod
    def search(
        db: Session,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedSearchResponse:
        """Search across CDR records (IMEI, IMSI, MSISDN, Cell ID),
        towers (CGI, CI), and cases (title, description).

        Uses parameterized LIKE queries — SQL injection safe by design.
        """
        pattern = f"%{query}%"

        # --- CDR Records: IMEI, IMSI, MSISDN (target_number), Cell ID (first_cgi, last_cgi) ---
        cdr_filter = or_(
            CDRRecord.imei.ilike(pattern),
            CDRRecord.imsi.ilike(pattern),
            CDRRecord.target_number.ilike(pattern),
            CDRRecord.first_cgi.ilike(pattern),
            CDRRecord.last_cgi.ilike(pattern),
        )
        cdr_query = db.query(CDRRecord).filter(cdr_filter)
        cdr_total = cdr_query.count()

        # --- Towers: CGI, CI ---
        tower_filter = or_(
            Tower.cgi.ilike(pattern),
            Tower.ci.ilike(pattern),
        )
        tower_query = db.query(Tower).filter(tower_filter)
        tower_total = tower_query.count()

        # --- Cases: title, description ---
        case_filter = or_(
            Case.title.ilike(pattern),
            Case.description.ilike(pattern),
        )
        case_query = db.query(Case).filter(case_filter)
        case_total = case_query.count()

        total = cdr_total + tower_total + case_total

        # Merge results with offset/limit across combined set
        # Order: CDR records → Towers → Cases
        results: list[CDRSearchResult | TowerSearchResult | CaseSearchResult] = []
        remaining_offset = offset
        remaining_limit = limit

        # Phase 1: CDR records
        if remaining_limit > 0 and remaining_offset < cdr_total:
            cdr_records = (
                cdr_query.order_by(CDRRecord.id)
                .offset(remaining_offset)
                .limit(remaining_limit)
                .all()
            )
            for record in cdr_records:
                results.append(CDRSearchResult.model_validate(record))
            remaining_limit -= len(cdr_records)
            remaining_offset = 0
        else:
            remaining_offset -= cdr_total
            remaining_offset = max(remaining_offset, 0)

        # Phase 2: Towers
        if remaining_limit > 0 and remaining_offset < tower_total:
            towers = (
                tower_query.order_by(Tower.id)
                .offset(remaining_offset)
                .limit(remaining_limit)
                .all()
            )
            for tower in towers:
                results.append(TowerSearchResult.model_validate(tower))
            remaining_limit -= len(towers)
            remaining_offset = 0
        else:
            remaining_offset -= tower_total
            remaining_offset = max(remaining_offset, 0)

        # Phase 3: Cases
        if remaining_limit > 0 and remaining_offset < case_total:
            cases = (
                case_query.order_by(Case.id)
                .offset(remaining_offset)
                .limit(remaining_limit)
                .all()
            )
            for case in cases:
                results.append(CaseSearchResult.model_validate(case))

        return PaginatedSearchResponse(
            results=results,
            total=total,
            limit=limit,
            offset=offset,
            query=query,
        )
