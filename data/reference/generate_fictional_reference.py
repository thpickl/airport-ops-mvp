from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config" / "demo_config.json").read_text(encoding="utf-8"))
AIRPORT_SNAPSHOT = json.loads((ROOT / "config" / "reference" / "airport-anchors.json").read_text(encoding="utf-8"))
SEED = int(CONFIG["random_seed"])
GENERATOR_VERSION = CONFIG["generator_version"]
SOURCE_AS_OF_DATE = "2026-08-09"
IATA_SOURCE_URL = "https://www.iata.org/en/publications/directories/code-search/"
ICAO_TYPE_SOURCE_URL = "https://www.icao.int/publications/DOC8643/Pages/Search.aspx"

AIRLINES = [
    ("Air France", "AF", "AFR", "France", "FR", "SkyTeam", "https://wwws.airfrance.fr/"),
    ("easyJet", "U2", "EZY", "United Kingdom", "GB", "Independent", "https://www.easyjet.com/"),
    ("Transavia France", "TO", "TVF", "France", "FR", "Air France-KLM Group", "https://www.transavia.com/"),
    ("Air Corsica", "XK", "CCM", "France", "FR", "Independent", "https://www.aircorsica.com/"),
    ("ITA Airways", "AZ", "ITY", "Italy", "IT", "Independent", "https://www.ita-airways.com/"),
    ("Ryanair", "FR", "RYR", "Ireland", "IE", "Independent", "https://www.ryanair.com/"),
    ("Wizz Air Malta", "W4", "WMT", "Malta", "MT", "Independent", "https://wizzair.com/"),
    ("Neos", "NO", "NOS", "Italy", "IT", "Independent", "https://www.neosair.com/"),
    ("Air Dolomiti", "EN", "DLA", "Italy", "IT", "Lufthansa Group", "https://www.airdolomiti.eu/"),
    ("TAP Air Portugal", "TP", "TAP", "Portugal", "PT", "Star Alliance", "https://www.flytap.com/"),
    ("Azores Airlines", "S4", "RZO", "Portugal", "PT", "Independent", "https://www.azoresairlines.pt/"),
    ("Portugalia Airlines", "NI", "PGA", "Portugal", "PT", "TAP Group", "https://www.flytap.com/"),
    ("Royal Jordanian", "RJ", "RJA", "Jordan", "JO", "oneworld", "https://www.rj.com/"),
    ("Jordan Aviation", "R5", "JAV", "Jordan", "JO", "Independent", "https://www.jordanaviation.jo/"),
    ("Lufthansa", "LH", "DLH", "Germany", "DE", "Star Alliance", "https://www.lufthansa.com/"),
    ("British Airways", "BA", "BAW", "United Kingdom", "GB", "oneworld", "https://www.britishairways.com/"),
    ("KLM Royal Dutch Airlines", "KL", "KLM", "Netherlands", "NL", "SkyTeam", "https://www.klm.com/"),
    ("Emirates", "EK", "UAE", "United Arab Emirates", "AE", "Independent", "https://www.emirates.com/"),
    ("Qatar Airways", "QR", "QTR", "Qatar", "QA", "oneworld", "https://www.qatarairways.com/"),
    ("Turkish Airlines", "TK", "THY", "Turkiye", "TR", "Star Alliance", "https://www.turkishairlines.com/"),
]

AIRCRAFT_MODELS = [
    ("BCS3", "Airbus", "A220-300", "Regional jet", 145, 35.10, 38.70, "C", 38, "https://aircraft.airbus.com/en/aircraft/a220/a220-300"),
    ("A319", "Airbus", "A319-100", "Narrow-body jet", 144, 35.80, 33.84, "C", 35, "https://aircraft.airbus.com/en/aircraft/a320-the-most-successful-aircraft-family-ever/a319ceo"),
    ("A320", "Airbus", "A320-200", "Narrow-body jet", 180, 35.80, 37.57, "C", 38, "https://aircraft.airbus.com/en/aircraft/a320-the-most-successful-aircraft-family-ever/a320ceo"),
    ("A20N", "Airbus", "A320neo", "Narrow-body jet", 186, 35.80, 37.57, "C", 38, "https://aircraft.airbus.com/en/aircraft/a320-the-most-successful-aircraft-family-ever/a320neo"),
    ("A21N", "Airbus", "A321neo", "Narrow-body jet", 220, 35.80, 44.51, "C", 42, "https://aircraft.airbus.com/en/aircraft/a320-the-most-successful-aircraft-family-ever/a321neo"),
    ("A332", "Airbus", "A330-200", "Wide-body jet", 253, 60.30, 58.82, "E", 65, "https://aircraft.airbus.com/en/aircraft/a330-advanced-to-boost-profitability/a330-200"),
    ("A339", "Airbus", "A330-900neo", "Wide-body jet", 287, 64.00, 63.66, "E", 70, "https://aircraft.airbus.com/en/aircraft/a330-advanced-to-boost-profitability/a330-900"),
    ("A359", "Airbus", "A350-900", "Wide-body jet", 325, 64.75, 66.80, "E", 75, "https://aircraft.airbus.com/en/aircraft/a350-clean-sheet-clean-start/a350-900"),
    ("AT76", "ATR", "ATR 72-600", "Regional turboprop", 72, 27.05, 27.17, "C", 30, "https://www.atr-aircraft.com/our-aircraft/atr-72-600/"),
    ("B738", "Boeing", "737-800", "Narrow-body jet", 189, 35.80, 39.50, "C", 40, "https://www.boeing.com/commercial/737ng"),
    ("B38M", "Boeing", "737 MAX 8", "Narrow-body jet", 189, 35.90, 39.52, "C", 40, "https://www.boeing.com/commercial/737max"),
    ("B788", "Boeing", "787-8", "Wide-body jet", 248, 60.10, 56.70, "E", 65, "https://www.boeing.com/commercial/787"),
    ("B789", "Boeing", "787-9", "Wide-body jet", 296, 60.10, 62.80, "E", 70, "https://www.boeing.com/commercial/787"),
    ("B77W", "Boeing", "777-300ER", "Wide-body jet", 396, 64.80, 73.90, "E", 80, "https://www.boeing.com/commercial/777"),
    ("E190", "Embraer", "E190", "Regional jet", 100, 28.72, 36.24, "C", 32, "https://www.embraercommercialaviation.com/commercial-jets/e190/"),
    ("E290", "Embraer", "E195-E2", "Regional jet", 146, 35.12, 41.50, "C", 35, "https://www.embraercommercialaviation.com/commercial-jets/e195-e2/"),
]


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUTPUT / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_airports() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for reference in AIRPORT_SNAPSHOT["records"]:
        code = reference["iata_code"]
        records.append({
            "airport_id": f"SYN-AP-{code}",
            "airport_reference_id": reference["airport_reference_id"],
            "iata_code": code,
            "icao_code": reference["icao_code"],
            "airport_name": reference["name"],
            "city": reference["city"],
            "country": reference["country"],
            "iso_country_code": reference["country_code"],
            "operating_region_id": f"SYN-REG-{reference['region'].upper()}",
            "iana_time_zone": reference["time_zone"],
            "latitude": reference["latitude"],
            "longitude": reference["longitude"],
            "elevation_ft": reference["elevation_ft"],
            "is_synthetic": False,
            "reference_anchor_only": True,
            "fictional_portfolio_relationship": True,
            "data_classification": "Public geographic reference",
            "source_name": "OurAirports open airport data and IANA Time Zone Database",
            "source_url": "https://ourairports.com/data/airports.csv",
            "source_as_of_date": AIRPORT_SNAPSHOT["snapshot_date"],
            "record_source": "CheckedInPublicReferenceSnapshot",
            "generator_version": GENERATOR_VERSION,
            "random_seed": SEED,
        })
    return records


def build_airlines() -> list[dict[str, Any]]:
    return [{
        "airline_id": f"REF-AL-{index:03d}",
        "iata_code": iata_code,
        "icao_code": icao_code,
        "airline_name": name,
        "home_country": home_country,
        "iso_country_code": country_code,
        "alliance": alliance,
        "reference_status": "ActiveReference",
        "is_synthetic": False,
        "data_classification": "PublicReference",
        "source_name": "IATA Airline Coding Directory and official airline website",
        "source_url": IATA_SOURCE_URL,
        "official_website": official_website,
        "source_as_of_date": SOURCE_AS_OF_DATE,
        "record_source": "CheckedInPublicReferenceCatalog",
        "validation_status": "VerifiedRequestedCatalog",
        "generator_version": GENERATOR_VERSION,
        "random_seed": SEED,
    } for index, (name, iata_code, icao_code, home_country, country_code, alliance, official_website) in enumerate(AIRLINES, start=1)]


def build_aircraft_types() -> list[dict[str, Any]]:
    return [{
        "aircraft_type_id": f"AC{index:02d}",
        "icao_type_designator": designator,
        "manufacturer": manufacturer,
        "model": model,
        "aircraft_category": category,
        "representative_seat_capacity": seats,
        "wingspan_m": wingspan,
        "length_m": length,
        "stand_category": stand_category,
        "representative_turnaround_target_min": turnaround,
        "operating_assumption_flag": True,
        "is_synthetic": False,
        "data_classification": "PublicReference",
        "operating_assumption_classification": "SyntheticMaster",
        "field_classification": {
            "identity_and_dimensions": "PublicReference",
            "representative_seat_capacity": "SyntheticMaster",
            "representative_turnaround_target_min": "SyntheticMaster",
            "stand_category": "DerivedAnalytical"
        },
        "source_name": "ICAO Doc 8643 and manufacturer aircraft characteristics",
        "source_url": ICAO_TYPE_SOURCE_URL,
        "manufacturer_source_url": manufacturer_source_url,
        "source_as_of_date": SOURCE_AS_OF_DATE,
        "record_source": "CheckedInPublicReferenceCatalog",
        "validation_status": "VerifiedRequestedCatalog",
        "generator_version": GENERATOR_VERSION,
        "random_seed": SEED,
    } for index, (designator, manufacturer, model, category, seats, wingspan, length, stand_category, turnaround, manufacturer_source_url) in enumerate(AIRCRAFT_MODELS, start=1)]


def main() -> None:
    airports = build_airports()
    airlines = build_airlines()
    aircraft_types = build_aircraft_types()
    country_time_zones = {
        "France": ("FR", ["Europe/Paris"]),
        "Italy": ("IT", ["Europe/Rome"]),
        "Portugal": ("PT", ["Europe/Lisbon", "Atlantic/Madeira"]),
        "Jordan": ("JO", ["Asia/Amman"]),
    }
    countries = [{
        "country_id": f"REF-COUNTRY-{code}",
        "country_name": name,
        "iso_country_code": code,
        "operating_region_id": f"SYN-REG-{name.upper()}",
        "iana_time_zones": time_zones,
        "is_synthetic": False,
        "data_classification": "PublicReference",
        "source_name": "Checked-in airport reference snapshot",
        "source_url": "repo://config/reference/airport-anchors.json",
        "source_as_of_date": AIRPORT_SNAPSHOT["snapshot_date"],
        "record_source": "CheckedInPublicReferenceSnapshot",
    } for name, (code, time_zones) in country_time_zones.items()]

    write_json("airports.json", {"schema_version": "5.0", "data_classification": "PublicReference", "source_as_of_date": AIRPORT_SNAPSHOT["snapshot_date"], "records": airports})
    write_json("airlines.json", {"schema_version": "4.0", "data_classification": "PublicReference", "source_as_of_date": SOURCE_AS_OF_DATE, "records": airlines})
    write_json("aircraft_types.json", {"schema_version": "4.0", "data_classification": "PublicReference", "source_as_of_date": SOURCE_AS_OF_DATE, "records": aircraft_types})
    write_json("countries.json", {"schema_version": "4.0", "data_classification": "PublicReference", "source_as_of_date": SOURCE_AS_OF_DATE, "records": countries})
    write_json("source_manifest.json", {
        "schema_version": "3.0",
        "source_as_of_date": SOURCE_AS_OF_DATE,
        "generator_version": GENERATOR_VERSION,
        "random_seed": SEED,
        "classification_policy": {
            "PublicReference": "Airport, country, airline, manufacturer, aircraft-type identity, public codes, dimensions, coordinates, elevation, and time zones.",
            "SyntheticMaster": "Fictional organization, portfolio relationship, facilities, people, fleets, seat assumptions, and turnaround targets.",
            "SyntheticOperational": "All schedules, routes, flights, events, telemetry, transactions, incidents, and outcomes.",
            "DerivedAnalytical": "All Silver/Gold enrichments, Warehouse/KQL products, semantic measures, forecasts, benchmarks, and recommendations."
        },
        "fictional_scope_statement": "Real airport identities are public reference anchors only. Ownership, infrastructure, operations, people, events, KPIs, recommendations, and outcomes are synthetic.",
        "sources": AIRPORT_SNAPSHOT["sources"] + [{
            "source_id": "SRC-SYNTHETIC-GENERATOR",
            "source_name": "Deterministic Synthetic Reference Generator",
            "source_url": "repo://data/reference/generate_fictional_reference.py",
            "used_for": ["fictional portfolio relationships and operational master data"]
        }, {
            "source_id": "SRC-IATA-CODE-SEARCH",
            "source_name": "IATA Airline Coding Directory",
            "source_url": IATA_SOURCE_URL,
            "source_as_of_date": SOURCE_AS_OF_DATE,
            "used_for": ["airline names and public IATA/ICAO codes"]
        }, {
            "source_id": "SRC-ICAO-DOC8643",
            "source_name": "ICAO Doc 8643 Aircraft Type Designators",
            "source_url": ICAO_TYPE_SOURCE_URL,
            "source_as_of_date": SOURCE_AS_OF_DATE,
            "used_for": ["aircraft type designators"]
        }]
    })
    print(f"Generated {len(airports)} airport, {len(airlines)} airline, and {len(aircraft_types)} aircraft-type public references")


if __name__ == "__main__":
    main()
