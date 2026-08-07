import math
from app.database.session import SessionLocal
from app.models.measurement import Measurement
from app.models.cdr_record import CDRRecord
from app.models.movement_event import MovementEvent
from app.models.tower import Tower


def main():
    db = SessionLocal()

    # Pre-fetch all towers into a map for fast lookup
    towers = db.query(Tower).all()
    tower_map = {
        t.tower_id: (t.latitude, t.longitude)
        for t in towers
        if t.latitude is not None and t.longitude is not None
    }

    # Get all measurements without a tower_id
    measurements = db.query(Measurement).filter(Measurement.tower_id.is_(None)).all()
    updated_count = 0

    for m in measurements:
        if m.measurement_code.startswith("IMP-"):
            # It's an imported measurement. Try to find the corresponding CDR record
            # We match by case_id and timestamp.
            cdr = (
                db.query(CDRRecord)
                .filter(
                    CDRRecord.case_id == m.case_id, CDRRecord.timestamp == m.timestamp
                )
                .first()
            )

            if cdr:
                cgi = cdr.first_cgi or cdr.last_cgi
                if cgi:
                    m.tower_id = cgi

                    # Also update corresponding MovementEvent's from_cgi
                    me = (
                        db.query(MovementEvent)
                        .filter(
                            MovementEvent.case_id == m.case_id,
                            MovementEvent.timestamp == m.timestamp,
                        )
                        .first()
                    )

                    if me and not me.from_cgi:
                        me.from_cgi = cgi

                    # Calculate estimated RSSI
                    if (
                        m.latitude is not None
                        and m.longitude is not None
                        and cgi in tower_map
                    ):
                        t_lat, t_lon = tower_map[cgi]

                        # Haversine distance
                        R = 6_371_000
                        dlat = math.radians(t_lat - m.latitude)
                        dlon = math.radians(t_lon - m.longitude)
                        a = (
                            math.sin(dlat / 2) ** 2
                            + math.cos(math.radians(m.latitude))
                            * math.cos(math.radians(t_lat))
                            * math.sin(dlon / 2) ** 2
                        )
                        dist_m = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                        dist_m = max(dist_m, 1.0)

                        # Log-distance path loss
                        est_rssi = round(
                            43.0 - 38.0 - 10.0 * 3.5 * math.log10(dist_m), 2
                        )
                        est_rssi = max(-150.0, min(0.0, est_rssi))

                        if m.rssi_dbm is None:
                            m.rssi_dbm = est_rssi

                    updated_count += 1

    db.commit()
    print(f"Updated {updated_count} measurements with tower_id and estimated RSSI.")


if __name__ == "__main__":
    main()
