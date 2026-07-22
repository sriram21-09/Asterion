"""Tower Intelligence Service
==========================

Provides database-backed cell tower lookup, CGI fallback resolution,
and confidence classification into three categories: Known (1.0), Estimated (0.6), and Unknown (0.2).
"""

from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.models.tower import Tower
from app.schemas.tower import TowerCreate, CGILookupResponse
from scientific.pipeline.benchmarks import parse_cgi, CGIResolver


class TowerIntelligenceService:
    """Service to handle tower registration, CGI coordinate resolution, and confidence scoring."""

    @staticmethod
    def classify_confidence(
        latitude: Optional[float],
        longitude: Optional[float],
        resolution_method: Optional[str] = None,
    ) -> Tuple[float, str]:
        """Enforce the 3 strict confidence categories:

        - Known (1.0): Direct parsed/exact coordinates available.
        - Estimated (0.6): Resolved via prefix fallback (LAC, MNC, MCC).
        - Unknown (0.2): Missing/null coordinates (Jio, Vi, or unresolved).
        """
        if latitude is None or longitude is None or resolution_method == "unresolved":
            return (0.2, "Unknown")
        elif resolution_method in (
            "prefix_lac",
            "prefix_mnc",
            "prefix_mcc",
            "estimated",
        ):
            return (0.6, "Estimated")
        else:
            return (1.0, "Known")

    @classmethod
    def register_tower(cls, db: Session, tower_data: TowerCreate) -> Tower:
        """Register a new tower in the database.

        WARNING: Jio and Vi towers without coordinates must be recorded with latitude = None and
        longitude = None with 0.2 confidence (Unknown). DO NOT default to (0,0).
        """
        # Parse CGI if string present
        cgi_str = tower_data.cgi
        mcc = tower_data.mcc
        mnc = tower_data.mnc
        lac = tower_data.lac
        ci = tower_data.ci

        if cgi_str and not (mcc and mnc and lac and ci):
            parsed = parse_cgi(cgi_str)
            mcc = mcc or parsed["mcc"]
            mnc = mnc or parsed["mnc"]
            lac = lac or parsed["lac"]
            ci = ci or parsed["ci"]
        elif (mcc and mnc and lac and ci) and not cgi_str:
            cgi_str = f"{mcc}-{mnc}-{lac}-{ci}"

        # Determine coordinates and confidence category
        lat = tower_data.latitude
        lon = tower_data.longitude

        # Check for explicitly missing / null coordinates
        if lat is None or lon is None:
            # Jio / Vi or missing coords -> recorded as null with 0.2 confidence
            lat = None
            lon = None
            res_method = "unresolved"
            confidence, category = cls.classify_confidence(lat, lon, res_method)
        else:
            lat = float(lat)
            lon = float(lon)
            res_method = tower_data.resolution_method or "exact"
            if (
                tower_data.confidence is not None
                and tower_data.confidence_category is not None
            ):
                confidence = tower_data.confidence
                category = tower_data.confidence_category
            else:
                confidence, category = cls.classify_confidence(lat, lon, res_method)

        db_tower = Tower(
            tower_name=tower_data.tower_name or cgi_str or "Tower",
            cgi=cgi_str,
            mcc=mcc,
            mnc=mnc,
            lac=lac,
            ci=ci,
            operator=tower_data.operator,
            latitude=lat,
            longitude=lon,
            sector=tower_data.sector,
            confidence=confidence,
            confidence_category=category,
            resolution_method=res_method,
        )

        db.add(db_tower)
        db.commit()
        db.refresh(db_tower)
        return db_tower

    @classmethod
    def resolve_cgi(cls, db: Session, cgi_str: str) -> CGILookupResponse:
        """Query database mappings to resolve CGI (MCC-MNC-LAC-CI) coordinates via prefix fallback hierarchy.

        Fallback Hierarchy:
          1. Exact Match (MCC-MNC-LAC-CI) -> Known (1.0)
          2. LAC Prefix Match (MCC-MNC-LAC centroid) -> Estimated (0.6)
          3. MNC Prefix Match (MCC-MNC centroid) -> Estimated (0.6)
          4. MCC Prefix Match (MCC centroid) -> Estimated (0.6)
          5. Unresolved -> Unknown (0.2)
        """
        parsed = parse_cgi(cgi_str)
        q_mcc = parsed["mcc"]
        q_mnc = parsed["mnc"]
        q_lac = parsed["lac"]
        q_ci = parsed["ci"]

        # Helper to compute centroid from matching DB towers with valid coordinates
        def query_centroid(
            mcc: str,
            mnc: Optional[str] = None,
            lac: Optional[str] = None,
            ci: Optional[str] = None,
        ):
            query = db.query(Tower).filter(
                Tower.latitude.isnot(None),
                Tower.longitude.isnot(None),
                Tower.mcc == mcc,
            )
            if mnc is not None:
                query = query.filter(Tower.mnc == mnc)
            if lac is not None:
                query = query.filter(Tower.lac == lac)
            if ci is not None:
                query = query.filter(Tower.ci == ci)

            towers = query.all()
            if not towers:
                return None, None, 0, None

            avg_lat = sum(t.latitude for t in towers) / len(towers)
            avg_lon = sum(t.longitude for t in towers) / len(towers)
            op = towers[0].operator if towers else None
            return avg_lat, avg_lon, len(towers), op

        # 1. Try Exact Match by full CGI or MCC-MNC-LAC-CI
        if cgi_str:
            exact_by_cgi = (
                db.query(Tower)
                .filter(
                    Tower.cgi == cgi_str,
                    Tower.latitude.isnot(None),
                    Tower.longitude.isnot(None),
                )
                .first()
            )
            if exact_by_cgi:
                conf, cat = cls.classify_confidence(
                    exact_by_cgi.latitude, exact_by_cgi.longitude, "exact"
                )
                return CGILookupResponse(
                    cgi=cgi_str,
                    resolved_latitude=exact_by_cgi.latitude,
                    resolved_longitude=exact_by_cgi.longitude,
                    confidence=conf,
                    confidence_category=cat,
                    resolution_method="exact",
                    matched_towers_count=1,
                    operator=exact_by_cgi.operator,
                )

        if q_mcc and q_mnc and q_lac and q_ci:
            lat, lon, count, op = query_centroid(q_mcc, q_mnc, q_lac, q_ci)
            if lat is not None and lon is not None:
                conf, cat = cls.classify_confidence(lat, lon, "exact")
                return CGILookupResponse(
                    cgi=cgi_str,
                    resolved_latitude=lat,
                    resolved_longitude=lon,
                    confidence=conf,
                    confidence_category=cat,
                    resolution_method="exact",
                    matched_towers_count=count,
                    operator=op,
                )

        # 2. Try LAC Prefix Fallback
        if q_mcc and q_mnc and q_lac:
            lat, lon, count, op = query_centroid(q_mcc, q_mnc, q_lac)
            if lat is not None and lon is not None:
                conf, cat = cls.classify_confidence(lat, lon, "prefix_lac")
                return CGILookupResponse(
                    cgi=cgi_str,
                    resolved_latitude=lat,
                    resolved_longitude=lon,
                    confidence=conf,
                    confidence_category=cat,
                    resolution_method="prefix_lac",
                    matched_towers_count=count,
                    operator=op,
                )

        # 3. Try MNC Prefix Fallback
        if q_mcc and q_mnc:
            lat, lon, count, op = query_centroid(q_mcc, q_mnc)
            if lat is not None and lon is not None:
                conf, cat = cls.classify_confidence(lat, lon, "prefix_mnc")
                return CGILookupResponse(
                    cgi=cgi_str,
                    resolved_latitude=lat,
                    resolved_longitude=lon,
                    confidence=conf,
                    confidence_category=cat,
                    resolution_method="prefix_mnc",
                    matched_towers_count=count,
                    operator=op,
                )

        # 4. Try MCC Prefix Fallback
        if q_mcc:
            lat, lon, count, op = query_centroid(q_mcc)
            if lat is not None and lon is not None:
                conf, cat = cls.classify_confidence(lat, lon, "prefix_mcc")
                return CGILookupResponse(
                    cgi=cgi_str,
                    resolved_latitude=lat,
                    resolved_longitude=lon,
                    confidence=conf,
                    confidence_category=cat,
                    resolution_method="prefix_mcc",
                    matched_towers_count=count,
                    operator=op,
                )

        # 5. Fall back to scientific CGIResolver in-memory fallback if registered towers exist in DB
        all_db_towers = db.query(Tower).all()
        if all_db_towers:
            resolver = CGIResolver(all_db_towers)
            res = resolver.resolve_cgi(cgi_str)
            if (
                res["resolved_latitude"] is not None
                and res["resolved_longitude"] is not None
            ):
                conf, cat = cls.classify_confidence(
                    res["resolved_latitude"],
                    res["resolved_longitude"],
                    res["resolution_method"],
                )
                return CGILookupResponse(
                    cgi=cgi_str,
                    resolved_latitude=res["resolved_latitude"],
                    resolved_longitude=res["resolved_longitude"],
                    confidence=conf,
                    confidence_category=cat,
                    resolution_method=res["resolution_method"],
                    matched_towers_count=res["matched_towers_count"],
                )

        # 6. Unresolved / missing coordinates -> Unknown (0.2) with null coordinates
        conf, cat = cls.classify_confidence(None, None, "unresolved")
        return CGILookupResponse(
            cgi=cgi_str,
            resolved_latitude=None,
            resolved_longitude=None,
            confidence=conf,
            confidence_category=cat,
            resolution_method="unresolved",
            matched_towers_count=0,
        )

    @classmethod
    def get_towers(
        cls,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        operator: Optional[str] = None,
        confidence_category: Optional[str] = None,
    ) -> List[Tower]:
        """Retrieve list of towers with optional filtering."""
        query = db.query(Tower)
        if operator:
            query = query.filter(Tower.operator == operator)
        if confidence_category:
            query = query.filter(Tower.confidence_category == confidence_category)
        return query.offset(skip).limit(limit).all()

    @classmethod
    def get_tower_by_cgi(cls, db: Session, cgi: str) -> Optional[Tower]:
        """Find a single tower by exact CGI."""
        return db.query(Tower).filter(Tower.cgi == cgi).first()

    @classmethod
    def bulk_resolve_cdr_records(cls, db: Session, cdr_records: List[Any]) -> List[Any]:
        """Enrich a list of CDR record dictionaries/objects with resolved coordinates and tower confidence metrics."""
        for rec in cdr_records:
            cell_id = getattr(rec, "cell_id", None) or (
                rec.get("cell_id") if isinstance(rec, dict) else None
            )
            cgi_val = (
                getattr(rec, "cgi", None)
                or (rec.get("cgi") if isinstance(rec, dict) else None)
                or cell_id
            )

            if cgi_val:
                res = cls.resolve_cgi(db, str(cgi_val))
                if isinstance(rec, dict):
                    if rec.get("latitude") is None:
                        rec["latitude"] = res.resolved_latitude
                        rec["longitude"] = res.resolved_longitude
                    rec["tower_confidence"] = res.confidence
                    rec["tower_confidence_category"] = res.confidence_category
                    rec["tower_resolution_method"] = res.resolution_method
                else:
                    if getattr(rec, "latitude", None) is None:
                        setattr(rec, "latitude", res.resolved_latitude)
                        setattr(rec, "longitude", res.resolved_longitude)
                    setattr(rec, "tower_confidence", res.confidence)
                    setattr(rec, "tower_confidence_category", res.confidence_category)
                    setattr(rec, "tower_resolution_method", res.resolution_method)
        return cdr_records
