# Synthetic Data Methodology

## Reproducibility contract

- Generator version: `4.0.0`
- Default seed: `39039`
- Fixed start: `2026-01-01T00:00:00Z`
- Default profile: `smoke`, 30 days, 18 airport anchors
- Identity: typed UUIDv5 plus `SYN-` business identifiers
- Serialization: sorted-key canonical JSON with no insignificant whitespace
- Checksums: SHA-256 over stable business-key ordering
- Time: UTC storage plus IANA airport zone, local timestamp, UTC offset, and DST fold

Changing the generator version, configuration, profile, airport snapshot, or seed intentionally changes the logical checksum. Wall-clock time is never a simulation input.

## Causal scenario

The simulator creates event records rather than KPI answer rows.

| Outcome | Baseline inputs | Improvement inputs | Smoke tolerance |
|---|---|---|---|
| Turnaround | Six service components total about 48 minutes | Reduced cleaning, catering, baggage, boarding, and coordination durations | baseline 47-49 min; improvement 38-40 min |
| Peak queues | Time-of-day demand peaks and baseline capacity factor 1.0 | Capacity factor 1.40 and demand smoothing 0.16 | p95 reduction 35-41% |
| Boarding window | Miss probability derives from queue wait and affected passengers | Lower waits reduce missed windows | baseline 32-36% |
| Retail | Footfall 0.58, conversion 0.33, basket EUR 36.40 | Footfall 0.60, conversion 0.37, basket EUR 38.35 | revenue/pax uplift 19-25% |
| Regulatory preparation | Annualized activity frequency targets 840 | Stable-ranked 78% of improvement events receive automated drafts | annualized 800-880; automation 73-83% |
| Energy | Passenger-linked benchmark multiplied by 1.26 | Factor reduced to 1.08 | baseline variance 23-29%; efficiency improvement >8% |

The validated smoke result is approximately 48.08 to 39.09 turnaround minutes, 38.03% p95 queue reduction, 22.2% revenue-per-passenger uplift, 79.4% regulatory automation, and 14.3% energy-per-passenger improvement. These are simulated outcomes, not guaranteed business results.

## Fault model

Bronze deterministically injects late arrivals, duplicate candidates, out-of-order markers, corrections, and malformed payloads according to the profile fault rate. Silver selects the highest record version, quarantines malformed or policy-invalid records, preserves lineage, and records quality counts. Replaying an already committed batch adds no ingestion records.

## Privacy

Passenger and employee identifiers are pseudonymous deterministic tokens. No names, addresses, passport data, phone numbers, payment credentials, or biometrics are generated. Retail recommendations are synthetic, opt-in, cohort based, and advisory. Data Agent output suppresses cohorts below 10.

> Real airport identities are used only as public geographic reference anchors. All ownership, infrastructure, flights, passengers, employees, operations, performance, incidents, commercial activity, recommendations, and outcomes are synthetic.