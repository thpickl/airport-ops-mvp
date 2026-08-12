# Persona Perspectives

All perspectives project the shared `AirportOpsSharedModel`; none duplicates data or bypasses curated Gold/Warehouse views. Legacy labels map as follows: CEO to Executive, CIO and IT Professional to IT, and Operational Excellence Executive (OEE) to Operations. OEE never means manufacturing Overall Equipment Effectiveness here.

## Airport

**Tables:** airport hierarchy, persona scorecard, baggage performance, customer experience, spatial context.

**Measures:** on-time departure, queue wait/throughput, baggage SLA and exceptions, satisfaction, NPS proxy, operational risk.

**Purpose:** whole-airport operational status and spatial bottleneck review.

## Airline

**Tables:** airline, route, airline route performance, baggage performance, customer experience.

**Measures:** On-Time Departure %, Load Factor %, Avg Turnaround, Synthetic Ticket Revenue, Mishandled Bags per 1,000, Customer Satisfaction.

**Purpose:** fictional airline/route comparisons without real airline or passenger data.

## Executive

**Tables:** airport, persona scorecard, airline route performance, retail performance, IT service health.

**Measures:** operational risk, on-time departure, synthetic ticket/retail revenue, customer satisfaction, Data Quality Pass %.

**Purpose:** network outcomes and exceptions; synthetic commercial indicators are always labeled as proxies.

## Operations

**Tables:** airport, route, turnaround phase performance, gate performance, terminal flow, baggage performance, workforce coverage, incidents.

**Measures:** Turnaround Milestone Adherence %, Avg Turnaround, Gate Utilization %, queue wait/throughput, baggage SLA, Staffing Coverage %, Incident Count.

**Purpose:** gate/stand operations, turnaround bottlenecks, passenger flow, baggage, and aggregate shift coverage.

## Maintenance

**Tables:** airport, asset reliability, maintenance events, workforce coverage, energy efficiency.

**Measures:** Asset Availability %, Anomalous Assets, Open Maintenance Items, maintenance anomaly count, Staffing Coverage %, energy intensity.

**Purpose:** reliability and work coverage. Recommendations remain advisory and do not control equipment or issue work orders.

## Commercial

**Tables:** airport, retail performance, customer experience, airline route performance.

**Measures:** Synthetic Net Retail Revenue, Synthetic Revenue per Departing Passenger, average basket proxy, transactions, Customer Satisfaction, Synthetic NPS.

**Purpose:** fictional concession and customer-experience analysis; values are not financial records.

## CustomerExperience

**Tables:** airport, route, passenger cohort, customer experience, passenger flow, baggage performance, incidents.

**Measures:** Customer Satisfaction, Synthetic NPS, complaints per 1,000 responses, recommendation acceptance, queue wait, baggage SLA.

**Purpose:** aggregate fictional journey experience and service-recovery analysis without exposing passenger-level records or identity.

## IT

**Tables:** IT service health, enterprise Data Agent context, asset state, incidents, deployment status, lineage.

**Measures:** Data Quality Pass %, failed products, late/quarantined records, Synthetic Capacity Usage %, Synthetic Cost Proxy Units, Recommendations Requiring Approval.

**Purpose:** run state, quality, freshness, lineage, security controls, and explicitly synthetic capacity/cost indicators.
