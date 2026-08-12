# GeoJSON Guide

`geospatial/generate_geojson.py` produces 12 stable EPSG:4326 FeatureCollections:

- public airport reference points;
- illustrative operating-region overview polygons;
- synthetic terminal and zone polygons;
- synthetic gate, stand, and asset points;
- synthetic routes and passenger/baggage flows;
- synthetic incident and energy heat points.

Coordinates use longitude/latitude order. Polygon rings are closed. Feature IDs are globally unique and stable for the same snapshot/configuration. Airport points set `reference_anchor_only=true` and `is_synthetic=false`; every other geometry sets `is_synthetic=true` and states that it is not a real layout, route, boundary, or operational location.

Validation checks layer presence, coordinate ranges, closure, feature-ID uniqueness, classification, and byte-for-byte PBIR resource packaging.