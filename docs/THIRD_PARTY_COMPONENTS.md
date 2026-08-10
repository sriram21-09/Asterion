# Third-Party Components & Originality Disclosure

In accordance with E-Rakshak Hackathon technical requirements, this document outlines all external dependencies, libraries, and components utilized by Asterion, as well as clarifying the team's original contributions.

## Open-Source Libraries

### Frontend
| Component | Purpose | License |
|-----------|---------|---------|
| **React 19** | Core UI library | MIT |
| **Vite** | Build tooling | MIT |
| **Tailwind CSS 4** | Styling | MIT |
| **Zustand** | State management | MIT |
| **Leaflet / React-Leaflet** | Geospatial map rendering | BSD-2-Clause / Hippocratic |
| **Lucide React** | Iconography | ISC |

### Backend / Scientific Engine
| Component | Purpose | License |
|-----------|---------|---------|
| **FastAPI** | REST API framework | MIT |
| **Uvicorn** | ASGI server | BSD-3-Clause |
| **SQLAlchemy** | Database ORM | MIT |
| **Alembic** | Database migrations | MIT |
| **Pydantic V2** | Data validation & schemas | MIT |
| **NumPy** | Vectorized matrix operations | BSD-3-Clause |
| **SciPy** | Levenberg-Marquardt optimization | BSD-3-Clause |
| **Pytest** | Testing framework | MIT |

## External APIs & Services

Asterion is designed for offline capability in secure environments. **It does not rely on active external APIs for core scientific processing.**

- **Map Tiles**: The frontend utilizes public OpenStreetMap (OSM) tile servers by default for map rendering. In a production environment, this can be swapped for an offline, on-premise tile server.

## Datasets

The `datasets/` folder contains structural examples of telecom operator CDRs (Airtel, BSNL, Jio, Vi). Any data populated in demo scenarios has been algorithmically synthesized or anonymized for demonstration purposes and does not contain PII or real-world classified intelligence.

## Originality Claim

The following core components represent original engineering and mathematical implementation by the Asterion Team:

- **The Asterion Scientific Engine (`scientific/`):** Custom implementation of multilateration, bounded Kalman filtering, and GDOP confidence modeling specifically tuned for noisy cellular geometries.
- **The Asterion REST API:** Custom FastAPI architecture bridging the scientific engine to a persistent SQLite store.
- **The Asterion Dashboard:** Original UI/UX built from the ground up using React and Tailwind CSS.
- **Evidence Integrity Engine:** The SHA-256 cryptographic linkage connecting input rows directly to calculated coordinates.
