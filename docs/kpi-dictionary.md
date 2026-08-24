# KPI Dictionary

All targets, thresholds, forecasts, benchmarks, emissions factors, commercial values, and outcomes below are synthetic case-study assumptions. They are unsuitable for real operational or financial decisions. The executable catalog is `gold_kpi_catalog`; domain aggregates are created by notebook 09.

| Domain | KPI | Grain | Formula | Unit | Synthetic target/benchmark | Caveat |
|---|---|---|---|---|---|---|
| Flight | On-time arrival | airport/day | arrivals <= scheduled + 15 min / flights | % | 90% | Synthetic schedule |
| Flight | On-time departure | airport/day | departures <= scheduled + 15 min / flights | % | 90% | Synthetic schedule |
| Flight | Arrival/departure delay | airport/day | average actual - scheduled UTC timestamp | min | 0 | Nonnegative generated delays |
| Turnaround | Average duration | airport/day | average turnaround end - start | min | narrow-body 38 | Representative target; configurations vary |
| Turnaround | Narrow-body average | airport | average turnaround for `Narrow-body jet` only | min | 38 | Fleet-wide average is not comparable to a narrow-body target |
| Scenario | Turnaround (scenario) | scenario/airport | aircraft target + avoidable gap x (1 - variance reduction) | min | 39 | Projection from baseline facts, not an observed outcome |
| Scenario | Peak queue wait (scenario) | scenario/airport | baseline peak wait x (1 - queue reduction) | min | -38% vs baseline | Projection; bounded by rostered staff availability |
| Scenario | Revenue per passenger (scenario) | scenario/airport | baseline revenue per passenger x (1 + conversion uplift) | proxy | +22% vs baseline | Projection on a synthetic revenue proxy |
| Scenario | Energy variance (scenario) | scenario/airport | load x (1 - controllable share x controllable reduction) vs gate-hour benchmark | % | towards zero | Only HVAC and lighting are treated as schedulable |
| Scenario | Outcome result | outcome measure | comparison of optimised value against recorded target | status | MET / NOT_MET | `NOT_EVALUATED` where a governance gate blocks modelling |
| Turnaround | Target attainment | airport/day | turns <= aircraft-type target / turns | % | 90% | Aircraft targets are assumptions |
| Turnaround | Milestone adherence | airport/day | on-plan milestones / milestones | % | 95% | Five generated milestones |
| Flight | Late-inbound contribution | airport/day | arrivals >15 min late / flights | % | <10% | Synthetic causal proxy |
| Gate/stand | Utilization | airport/day | occupied minutes / 1,440 per resource | % | 65-85% | Single-day demonstration |
| Gate | Conflict count | airport/day | overlapping occupied intervals at same gate | count | 0 | Generated, not AODB conflict data |
| Passenger | Queue length/wait/throughput | airport/day | average/max/sum interval observations | pax, min, pax | wait <15 min | Aggregate PII-free observations |
| Passenger | Predicted congestion risk | airport/day | intervals with wait >=15 min / intervals | % forecast | <15% | Rule-based synthetic forecast |
| Passenger | Boarding-window risk | airport/day | watch boarding events / boarding events | % forecast | <10% | Synthetic boarding window |
| Passenger | Missed-connection risk | airport/day | arrivals >30 min late / flights | % forecast | <8% | Synthetic 45-minute connection assumption |
| Baggage | Bags processed/per flight | airport/day | bag count; bag count / flights | count, bags/flight | none | Synthetic tokens only |
| Baggage | Mishandled rate | airport/day | exception bags / bags * 1,000 | per 1,000 | 8 | Synthetic benchmark |
| Baggage | Transfer risk | airport/day | journeys >120 min or exception / bags | % forecast | <10% | Synthetic transfer assumption |
| Baggage | Delivery time | airport/day | average reclaim - load | min | <180 | Illustrative journey |
| Baggage | Scan completeness | airport/day | observed scans / expected scans, capped 100 | % | 99% | Synthetic scan events |
| Workforce | Planned/actual/overtime | airport/day | sums from pseudonymous roster | hours | overtime <5% | No workforce identity |
| Workforce | Roster coverage | airport/day | rows with actual >=90% planned / roster rows | % | 95% | Aggregate staffing proxy |
| Workforce | Skill coverage | airport/day | workers with mapped skill / workers | % | 100% | Synthetic skills |
| Workforce | Tasks per team | airport/day | ramp tasks / work teams | count | balanced | Synthetic workload |
| Workforce | Recommendation variance | airport/day | actual - planned hours | hours | 0 | Advisory; never assigns staff |
| Maintenance | Asset availability | airport/day | average availability observations | % | 98% | Synthetic telemetry |
| Maintenance | Failure/anomaly count | airport/day | anomalous observations | count | 0 | Failure proxy |
| Maintenance | MTBF | airport/day | observation hours / max(failures,1) | hours | rising | Demonstration approximation |
| Maintenance | MTTR | airport/day | average work-order resolution duration | hours | <12 | Synthetic work orders |
| Maintenance | Preventive compliance | airport/day | closed preventive / preventive work orders | % | 95% | Scenario status |
| Maintenance | Backlog | airport/day | work orders not Closed | count | 0 | No CMMS write-back |
| Maintenance | Predicted failure risk | airport/day | anomalous observations / observations | % forecast | <5% | Rule-based synthetic forecast |
| Energy | Total/intensity | airport/day | sum kWh; total / pax; total / flights | kWh | 450 kWh/flight | Synthetic benchmark |
| Energy | Peak demand | airport/day | max generated meter reading | kWh proxy | none | Not demand telemetry |
| Energy | Benchmark variance | airport/day | (kWh/flight - 450) / 450 | % | <=0% | Synthetic benchmark |
| Energy | Estimated emissions | airport/day | kWh * 0.233 | kg CO2e proxy | none | Synthetic factor, not inventory |
| Commercial | Revenue | airport/day | gross POS proxy - refund proxy | proxy units | none | Not currency/financial records |
| Commercial | Revenue per passenger | airport/day | net revenue proxy / passengers | proxy/pax | 8.50 | Synthetic European-style benchmark, not market evidence |
| Commercial | Transactions/conversion | airport/day | transactions / pax; capped at 100% | rate, % | scenario | Aggregate synthetic POS |
| Commercial | Average transaction | airport/day | gross proxy / transactions | proxy units | scenario | Not payment data |
| Commercial | Outlet performance | airport/day | net proxy / outlets | proxy units | scenario | Fictional concessions |
| Incident | Count/rate/severity | airport/day | count; count / flights *100; counts by severity | count/rate | scenario | Synthetic incidents, no vulnerability detail |
| Incident | Resolution time | airport/day | resolved incident delay proxy average | min proxy | scenario | Not case-management telemetry |
| CX | Satisfaction/NPS | airport/day | respondent-weighted aggregates | score | scenario | Synthetic surveys, no respondent identity |
| CX | Complaint rate | airport/day | responses with score <3 / responses *1,000 | per 1,000 | scenario | Synthetic proxy |
| Recommendation | Acceptance | airport/day | AcceptedForScenario / recommendations | % | 70% | Human-reviewed scenario outcome |
