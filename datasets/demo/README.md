# Asterion Demo Dataset

Curated demonstration dataset containing representative CDR (Call Detail Record) samples from all four supported Indian telecom operators.

## Dataset Contents

| File | Operator | Records | Description |
|------|----------|---------|-------------|
| `demo_airtel.csv` | Airtel (Bharti) | 25 | Sampled from 1,570 total records |
| `demo_bsnl.csv` | BSNL | 29 | Complete dataset (29 total records) |
| `demo_jio.csv` | Jio (Reliance) | 25 | Sampled from 7,101 total records |
| `demo_vi.csv` | Vi (Vodafone Idea) | 25 | Sampled from 4,134 total records |
| `asterion_demo_dataset.csv` | **All operators** | ~104 | Combined dataset |

## Column Schema

| Column | Type | Description |
|--------|------|-------------|
| `operator` | string | Telecom operator identifier (`airtel`, `bsnl`, `jio`, `vi`) |
| `target_number` | string | Subscriber phone number (A-party) |
| `b_party_number` | string | Other party phone number (B-party) |
| `call_type` | string | Event type (`IN`, `OUT`, `SMT`, `SMS`, etc.) |
| `timestamp` | ISO 8601 | Event timestamp |
| `duration` | integer | Call duration in seconds |
| `latitude` | float | WGS84 latitude of the cell site |
| `longitude` | float | WGS84 longitude of the cell site |
| `first_cgi` | string | Cell Global Identity (MCC-MNC-LAC-CI) of the start cell |
| `first_bts_location` | string | BTS location description / address |
| `last_cgi` | string | Cell Global Identity of the end cell |
| `imei` | string | International Mobile Equipment Identity |

## Sampling Strategy

Records are selected to ensure temporal and spatial diversity:
- **First 5 records** — earliest activity
- **Last 5 records** — latest activity  
- **15 evenly-spaced records** — middle-range coverage

For BSNL (29 records total), all records are included without sampling.

## Usage

```python
import pandas as pd

# Load combined demo dataset
df = pd.read_csv("datasets/demo/asterion_demo_dataset.csv")

# Filter by operator
airtel_df = df[df["operator"] == "airtel"]
jio_df = df[df["operator"] == "jio"]
```

## Generation

To regenerate this dataset from the source operator files:

```bash
python scripts/generate_demo_dataset.py
```

## Source Data

Original operator CDR files are located in `E-Rakshak CDR & Location Data Sets/`:
- `9714499703_Airtel.csv` (383 KB, 1,570 records)
- `9477523061_BSNL.csv` (6.5 KB, 29 records)
- `9877535365_Jio.csv` (1.0 MB, 7,101 records)
- `8980261614_Vi.csv` (1.9 MB, 4,134 records)
