# Report Catalog

The PBIR project contains 11 persona pages and 14 detail pages. Every generated page includes the required synthetic-data disclaimer, fixed data-as-of metadata, accessible alternative text, filters, and an advisory-AI notice.

| Persona page | Primary scope | Security scope |
|---|---|---|
| Executive | network outcomes and risk | group |
| Regional | region comparison | authorized regions |
| Airport | airport flow, baggage, and experience | authorized airports |
| Airline | synthetic airline performance | authorized airline |
| Operations | flight, turnaround, gate, and queue | authorized airports |
| Maintenance | asset health and work orders | authorized airports |
| Commercial | synthetic retail performance | authorized airports |
| Sustainability | energy, water, and emissions proxies | authorized airports/regions |
| Compliance | incidents and regulatory preparation | authorized airports/regions |
| Customer Experience | synthetic CSAT/NPS and recovery | aggregate only |
| IT | quality, freshness, lineage, security | platform |

Detail pages cover group overview, airport comparison, flight performance, turnaround, passenger flow, baggage, gates/stands, workforce, maintenance/digital twin, energy, retail, incidents, customer experience, and data quality/platform operations.

Azure Maps consumes packaged GeoJSON. Where a target PBIR schema or tenant policy does not accept a configured layer, the report retains latitude/longitude and packaged resources as the supported fallback; it must not be described as deployed Azure Maps until target validation succeeds.