# Azure Maps Portable Spatial Layers

> Every airport centroid, terminal, zone, gate, stand, flow, heat-map, and incident geometry is fictional and illustrative; none represents real airport geometry, routes, security boundaries, or operating areas. No Azure Maps account or endpoint is called.

| File | Geometry | Features | Join keys |
|---|---|---|---|
| `airports.geojson` | Point | 18 | `airport_id` |
| `operating_regions.geojson` | Polygon | 4 | `region_id` |
| `terminals.geojson` | Polygon | 36 | `airport_id`, `terminal_id` |
| `zones.geojson` | Polygon | 72 | `airport_id`, `terminal_id`, `zone_id` |
| `gates.geojson` | Point | 108 | `airport_id`, `gate_id`, `stand_id` |
| `stands.geojson` | Point | 108 | `airport_id`, `stand_id`, `gate_id` |
| `routes.geojson` | LineString | 18 | `airport_id`, `route_id` |
| `passenger_flows.geojson` | LineString | 36 | `airport_id`, `terminal_id` |
| `baggage_flows.geojson` | LineString | 18 | `airport_id` |
| `assets.geojson` | Point | 108 | `airport_id`, `asset_id` |
| `energy.geojson` | Point/heat feature | 108 | `airport_id`, `gate_id` |
| `incidents.geojson` | Point | 54 | `airport_id`, `incident_id` |

Feature counts and per-file SHA-256 digests are recorded in `geojson-manifest.json`.

`geospatial/generate_geojson.py` deterministically generates the files and `geojson-manifest.json`. Notebook `04` produces the relational spatial model and `dim_location` using the same stable keys.

## Future Azure Maps use

1. Create a governed Azure Maps resource outside this MVP; keep credentials out of source control.
2. Upload or host the GeoJSON through an approved private data path, or load the FeatureCollections directly in a client map control.
3. Style by `feature_type`, `operational_status`, or `area_type`; join live/curated status only through Gold/Warehouse views.
4. Preserve the synthetic banner in every map and report.

These files are visual context, not indoor-navigation, emergency-routing, or safety-control data.
