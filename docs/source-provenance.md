# Source Provenance and Classification

## Generator provenance

Airport names, cities, countries, IATA/ICAO codes, approximate WGS84 points, and elevations are snapshotted from OurAirports; IANA time-zone identifiers are assigned by locality. Retrieval date, URLs, usage notes, field provenance, and source-validation status are stored in `config/reference/airport-anchors.json`.

The default generated catalog contains:

- 18 public airport geographic reference anchors across France, Italy, Portugal, and Jordan.
- 20 fictional airlines with non-official synthetic codes.
- 16 fictional aircraft types with representative synthetic dimensions, capacity, stand category, and turnaround targets.
- Four fictional operating-region relationships based on country, with sourced IANA time zones.

`data/reference/source_manifest.json` records public sources and the deterministic synthetic generator. No real operational source is accessed.

## Synthetic master data

The organization, headquarters, portfolio relationships, airlines, aircraft instances, facilities, fleets, employees, skills, shifts, assets, outlets, and products are synthetic master data. Airport identities and points are classified as public geographic reference.

## Synthetic operational data

Routes, schedules, flights, passengers, customers, bookings, boarding, baggage, queues, ramp tasks, rosters, work orders, POS, weather, energy, incidents, surveys, recommendations, approvals, quality cases, and lineage events are generated operational data.

## Derived analytical data

Silver conformed tables, Gold facts/dimensions/aggregates, Warehouse/KQL views, TMDL measures, PBIR values, forecasts, targets, benchmarks, risk scores, and recommendations are derived exclusively from synthetic data.

## Metadata contract

Where applicable, records include `is_synthetic`, `data_classification`, `source_name`, `source_url`, `source_as_of_date`, `generated_at_utc`, `generator_version`, `random_seed`, `batch_id`, and `record_source`. Generation timestamps are audit metadata and excluded from deterministic business fingerprints.
