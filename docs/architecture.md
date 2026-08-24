# Extended Architecture

All dimensions, relationships, operating data, coordinates, analytical outputs, and twin state are deterministic fictional data generated from configuration and seed.

## 1. End-to-end architecture

```mermaid
flowchart LR
    Ref[Fictional region / airport / airline / aircraft catalogs] --> N01[01 Generate references + operations]
    Edge[Synthetic source-shaped domains\nflight / baggage / queue / POS / asset] --> N01
    Config[config/base/platform.json\nseed 42 / fixed date] --> N01
    Config --> N04[04 Physical + spatial]
    N01 --> Bronze[(Bronze Delta\nreplayable source shape)]
    Bronze --> N02[02 Clean + conform]
    N02 --> Silver[(Silver Delta\ndimensions / facts)]
    Silver --> N03[03 Base Gold]
    Silver --> N04
    N03 --> N05[05 Extended Gold + agent context]
    N04 --> N05
    N07[07 Enterprise Bronze] --> N08[08 Enterprise Silver]
    N08 --> N09[09 Enterprise Gold]
    N05 --> Gold[(Gold Delta\npersona / spatial / reliability / IT)]
    N09 --> Gold
    Gold --> WH[AirportOpsWarehouse\ncurated ops views]
    WH --> SM[AirportOpsSharedModel\n11 persona perspectives / 29 tables]
    WH --> Agent[Fabric Data Agent grounding]
    DTDL[DTDL + sample graph] -. optional notebook 14 .-> ADT[Azure Digital Twins]
    Geo[GeoJSON spatial layers] --> Maps[PBIR Azure Maps visuals]
    N05 --> AgentContext[agent_context\nadvisory + provenance + approval]
    AgentContext --> Agent
    N06[06 Validation] --> Bronze
    N06 --> Silver
    N06 --> Gold
```

## 2. Medallion data flow

```mermaid
flowchart TB
    subgraph Bronze[Bronze: source-shaped and replayable]
      B1[operations and events]
      B2[airport spatial / terminal zones]
      B3[asset registry / twin relationships]
    end
    subgraph Silver[Silver: typed, deduplicated, conformed]
      D[conformed dimensions]
      F[operational facts]
      P[physical dimensions + bridges]
      T[asset state + zone occupancy]
    end
    subgraph Gold[Gold: business-ready]
      G1[airport / executive health]
      G2[terminal / gate / flow]
      G3[asset reliability / energy]
      G4[spatial status / IT service health]
      G5[agent_context]
    end
    B1 --> D
    B1 --> F
    B2 --> P
    B3 --> P
    P --> T
    F --> G1
    F --> G2
    T --> G2
    T --> G3
    P --> G4
    G1 --> G5
    G2 --> G5
    G3 --> G5
    G4 --> G5
```

## 3. Physical and spatial hierarchy

```mermaid
flowchart TD
    Airport -->|contains| Terminal
    Terminal -->|contains| Zone
    Terminal -->|contains| Gate
    Zone -->|contains| Checkpoint
    Zone -->|contains| Asset
    Gate -->|serves / adjacent to| Stand
    Asset -->|monitored by| EnergyMeter
    Asset -->|located in| Zone
    Gate -->|located in| Terminal
    Location[dim_location / GeoJSON] -. spatial reference .-> Airport
    Location -. spatial reference .-> Terminal
    Location -. spatial reference .-> Zone
    Location -. spatial reference .-> Checkpoint
    Location -. spatial reference .-> Gate
    Location -. spatial reference .-> Stand
    Location -. spatial reference .-> Asset
```

## 4. Warehouse star schema

```mermaid
flowchart LR
    Date[dim_date] --> Turn[fact_turnaround]
    Time[dim_time] --> Turn
    Airport[dim_airport] --> Terminal[dim_terminal]
    Airport --> Gate[dim_gate]
    Terminal --> Zone[dim_zone]
    Zone --> Checkpoint[dim_checkpoint]
    Zone --> Asset[dim_asset]
    Gate --> Stand[dim_stand]
    Gate --> Turn
    Airline[dim_airline] --> Turn
    Aircraft[dim_aircraft] --> Turn
    Checkpoint --> Flow[fact_zone_occupancy]
    Asset --> State[fact_asset_state]
    Gate --> Energy[fact_energy_metering]
    Gate --> Maint[fact_maintenance]
    Gate --> Incident[fact_incident]
    Turn --> GateGold[gate performance]
    Flow --> TerminalGold[terminal flow]
    State --> AssetGold[asset reliability]
    GateGold --> Context[data agent grounding]
    AssetGold --> Context
```

## 5. Ontology relationships

```mermaid
flowchart LR
    Airport --> Terminal --> Zone --> Checkpoint
    Terminal --> Gate --> Stand
    Flight --> Gate
    Flight --> Turnaround
    Airline --> Flight
    Aircraft --> Flight
    Incident[OperationalIncident] --> Turnaround
    Zone --> PassengerFlowObservation
    Zone --> Asset --> MaintenanceEvent
    ServiceTeam --> MaintenanceEvent
    Airport --> EnergyObservation
    Airport --> WeatherObservation
    KPI --> Airport
    Recommendation --> Airport
    Recommendation --> Gate
    Recommendation --> Zone
    Recommendation --> Asset
```

## 6. Agent grounding and human approval

```mermaid
flowchart TD
    Q[Persona question] --> Resolve[Resolve terms and time grain]
    Resolve --> Curated[Query Gold / ops curated views only]
    Curated --> Evidence[Build answer + KPI evidence]
    Evidence --> Provenance[Attach view names, keys, as-of time]
    Provenance --> Advisory{Consequential recommendation?}
    Advisory -->|No| Answer[Return advisory answer]
    Advisory -->|Yes| Approval[State human approval required]
    Approval --> Human[Authorized human reviews]
    Human -->|Approve outside agent| External[Existing governed operating process]
    Human -->|Reject / insufficient data| Stop[No action; record limitation]
    Curated -->|missing / stale| Refuse[State limitation; do not infer]
```

## 7. Deployment and validation control plane

```mermaid
  flowchart LR
    Bundle[Mounted repository bundle] --> Bootstrap[00 Bootstrap items and notebooks]
    Bootstrap --> Lakehouse
    Bootstrap --> Warehouse
    Bootstrap --> Eventhouse
    Bootstrap --> KQLDB[KQL Database]
    Bootstrap --> Orchestrator[11 Job orchestration]
    Orchestrator --> Preflight[00 Validate prerequisites]
    Preflight --> Pass1[First deterministic pass]
    Pass1 --> Baseline[12 Fingerprint baseline]
    Baseline --> Pass2[Second deterministic pass]
    Pass2 --> Compare[12 Required fingerprint comparison]
    Compare --> Serving[10 SQL / KQL / TMDL / PBIR]
    Serving --> Status[15 Read-only status]
    Status --> Ledger[Deployment and validation evidence]
    Ledger --> Reset[13 Scoped reset / teardown]
```

Required core APIs are fail-fast. Data Agent/Fabric app item definitions are capability-checked; Rayfin remains a disabled configurable module when no native API is available.
