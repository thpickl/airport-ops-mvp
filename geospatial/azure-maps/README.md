# Azure Maps Portable Spatial Layers

> Every airport centroid, terminal, zone, gate, stand, flow, heat-map, and incident geometry is fictional and illustrative; none represents real airport geometry, routes, security boundaries, or operating areas. No Azure Maps account or endpoint is called.

| File | Geometry | Join keys |
|---|---|---|
| `airports.geojson` | Point | `airport_id` |
| `terminals.geojson` | Polygon | `airport_id`, `terminal_id` |
| `zones.geojson` | Polygon | `airport_id`, `terminal_id`, `zone_id` |
| `gates.geojson` | Point | `airport_id`, `gate_id`, `stand_id` |
| `stands.geojson` | Point | `airport_id`, `stand_id`, `gate_id` |
| `passenger_flows.geojson` | LineString | `airport_id`, `terminal_id` |
| `baggage_flows.geojson` | LineString | `airport_id` |
| `energy.geojson` | Point/heat feature | `airport_id`, `gate_id` |
| `incidents.geojson` | Point | `airport_id`, `incident_id` |

`geospatial/generate_geojson.py` deterministically generates the files and `geojson-manifest.json`. Notebook `04` produces the relational spatial model and `dim_location` using the same stable keys.

## Future Azure Maps use

1. Create a governed Azure Maps resource outside this MVP; keep credentials out of source control.
2. Upload or host the GeoJSON through an approved private data path, or load the FeatureCollections directly in a client map control.
3. Style by `feature_type`, `operational_status`, or `area_type`; join live/curated status only through Gold/Warehouse views.
4. Preserve the synthetic banner in every map and report.

These files are visual context, not indoor-navigation, emergency-routing, or safety-control data.
