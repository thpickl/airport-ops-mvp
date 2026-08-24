from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SH, SKOS, XSD


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = ROOT / "ontology"
ONTOLOGY_PATH = ONTOLOGY_DIR / "airport-operations.ttl"
RDF_XML_PATH = ONTOLOGY_DIR / "airport-operations.rdf"
SHACL_PATH = ONTOLOGY_DIR / "airport-operations.shacl.ttl"
INSTANCE_PATH = ONTOLOGY_DIR / "instances" / "airport-operations-sample.ttl"

ONTOLOGY_IRI = URIRef("https://data.fictional-airport-group.example/airport-operations/ontology")
VERSION_IRI = URIRef("https://data.fictional-airport-group.example/airport-operations/ontology/1.0.0")
AO = Namespace(str(ONTOLOGY_IRI) + "#")
RES = Namespace("https://data.fictional-airport-group.example/airport-operations/resource/")
PROV = Namespace("http://www.w3.org/ns/prov#")
QUDT = Namespace("http://qudt.org/schema/qudt/")

VERSION = "1.0.0"
ISSUED_DATE = "2026-08-13"


def words(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).replace("K P I", "KPI")


def bind_prefixes(graph: Graph) -> None:
    graph.bind("ao", AO)
    graph.bind("res", RES)
    graph.bind("dcterms", DCTERMS)
    graph.bind("owl", OWL)
    graph.bind("prov", PROV)
    graph.bind("qudt", QUDT)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("sh", SH)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)


def add_rdf_list(graph: Graph, identifier: str, values: list[URIRef]) -> BNode:
    head = BNode(identifier)
    current = head
    for index, value in enumerate(values):
        graph.add((current, RDF.first, value))
        next_node = RDF.nil if index == len(values) - 1 else BNode(f"{identifier}-{index + 1}")
        graph.add((current, RDF.rest, next_node))
        current = next_node
    return head


def add_class(
    graph: Graph,
    name: str,
    parent: str | None,
    comment: str,
    *,
    source_table: str | None = None,
    source_view: str | None = None,
    grain: str | None = None,
    primary_key: str | None = None,
    foreign_keys: tuple[str, ...] = (),
    scd: str | None = None,
) -> URIRef:
    node = AO[name]
    graph.add((node, RDF.type, OWL.Class))
    graph.add((node, RDFS.label, Literal(words(name), lang="en")))
    graph.add((node, RDFS.comment, Literal(comment, lang="en")))
    graph.add((node, RDFS.isDefinedBy, ONTOLOGY_IRI))
    if parent:
        graph.add((node, RDFS.subClassOf, AO[parent]))
    for predicate, value in (
        (AO.sourceTable, source_table),
        (AO.sourceView, source_view),
        (AO.warehouseGrain, grain),
        (AO.primaryKey, primary_key),
        (AO.scdSemantics, scd),
    ):
        if value:
            graph.add((node, predicate, Literal(value)))
    for foreign_key in foreign_keys:
        graph.add((node, AO.foreignKey, Literal(foreign_key)))
    return node


def add_object_property(
    graph: Graph,
    name: str,
    label: str,
    comment: str,
    domain: str,
    range_name: str,
    *,
    inverse: str | None = None,
    parent: str | None = None,
    functional: bool = False,
    transitive: bool = False,
) -> URIRef:
    node = AO[name]
    graph.add((node, RDF.type, OWL.ObjectProperty))
    graph.add((node, RDFS.label, Literal(label, lang="en")))
    graph.add((node, RDFS.comment, Literal(comment, lang="en")))
    graph.add((node, RDFS.domain, AO[domain]))
    graph.add((node, RDFS.range, AO[range_name]))
    graph.add((node, RDFS.isDefinedBy, ONTOLOGY_IRI))
    if inverse:
        graph.add((node, OWL.inverseOf, AO[inverse]))
    if parent:
        graph.add((node, RDFS.subPropertyOf, AO[parent]))
    if functional:
        graph.add((node, RDF.type, OWL.FunctionalProperty))
    if transitive:
        graph.add((node, RDF.type, OWL.TransitiveProperty))
    return node


def add_datatype_property(
    graph: Graph,
    name: str,
    label: str,
    comment: str,
    domain: str,
    datatype: URIRef,
    *,
    parent: str | None = None,
    functional: bool = False,
) -> URIRef:
    node = AO[name]
    graph.add((node, RDF.type, OWL.DatatypeProperty))
    graph.add((node, RDFS.label, Literal(label, lang="en")))
    graph.add((node, RDFS.comment, Literal(comment, lang="en")))
    graph.add((node, RDFS.domain, AO[domain]))
    graph.add((node, RDFS.range, datatype))
    graph.add((node, RDFS.isDefinedBy, ONTOLOGY_IRI))
    if parent:
        graph.add((node, RDFS.subPropertyOf, AO[parent]))
    if functional:
        graph.add((node, RDF.type, OWL.FunctionalProperty))
    return node


def add_exact_cardinality(graph: Graph, class_name: str, property_name: str, range_name: str, count: int = 1) -> None:
    restriction = BNode(f"restriction-{class_name}-{property_name}-exactly-{count}")
    graph.add((AO[class_name], RDFS.subClassOf, restriction))
    graph.add((restriction, RDF.type, OWL.Restriction))
    graph.add((restriction, OWL.onProperty, AO[property_name]))
    graph.add((restriction, OWL.qualifiedCardinality, Literal(count, datatype=XSD.nonNegativeInteger)))
    graph.add((restriction, OWL.onClass, AO[range_name]))


def add_min_cardinality(graph: Graph, class_name: str, property_name: str, range_name: str, count: int = 1) -> None:
    restriction = BNode(f"restriction-{class_name}-{property_name}-minimum-{count}")
    graph.add((AO[class_name], RDFS.subClassOf, restriction))
    graph.add((restriction, RDF.type, OWL.Restriction))
    graph.add((restriction, OWL.onProperty, AO[property_name]))
    graph.add((restriction, OWL.minQualifiedCardinality, Literal(count, datatype=XSD.nonNegativeInteger)))
    graph.add((restriction, OWL.onClass, AO[range_name]))


def add_key(graph: Graph, class_name: str, property_names: tuple[str, ...]) -> None:
    key_list = add_rdf_list(graph, f"key-{class_name}", [AO[name] for name in property_names])
    graph.add((AO[class_name], OWL.hasKey, key_list))


def build_ontology_graph() -> Graph:
    graph = Graph()
    bind_prefixes(graph)

    graph.add((ONTOLOGY_IRI, RDF.type, OWL.Ontology))
    graph.add((ONTOLOGY_IRI, OWL.versionIRI, VERSION_IRI))
    graph.add((ONTOLOGY_IRI, OWL.versionInfo, Literal(VERSION)))
    graph.add((ONTOLOGY_IRI, DCTERMS.title, Literal("Airport Operations Fabric Ontology", lang="en")))
    graph.add((ONTOLOGY_IRI, DCTERMS.description, Literal(
        "OWL 2 ontology for the repository's airport physical hierarchy, operational events, warehouse star schema, and governed measures.",
        lang="en",
    )))
    graph.add((ONTOLOGY_IRI, DCTERMS.issued, Literal(ISSUED_DATE, datatype=XSD.date)))
    graph.add((ONTOLOGY_IRI, DCTERMS.modified, Literal(ISSUED_DATE, datatype=XSD.date)))
    graph.add((ONTOLOGY_IRI, DCTERMS.license, URIRef("https://opensource.org/license/mit")))
    graph.add((ONTOLOGY_IRI, PROV.wasDerivedFrom, URIRef("urn:repo:fabric-airport-ops-mvp")))
    graph.add((ONTOLOGY_IRI, AO.schemaVersion, Literal(VERSION)))
    graph.add((ONTOLOGY_IRI, AO.generatorVersion, Literal("1.0.0")))
    graph.add((ONTOLOGY_IRI, AO.sourceArtifact, Literal("ontology/generate_ontology.py")))

    annotation_properties = {
        "sourceArtifact": "Repository artifact from which a term is derived.",
        "sourceTable": "Lakehouse Delta table implementing a mapped concept or analytical record.",
        "sourceView": "Curated Fabric Warehouse view exposing a mapped concept or analytical record.",
        "warehouseGrain": "Human-readable relational grain copied from executable source or repository documentation.",
        "primaryKey": "Primary or business key documented by the repository.",
        "foreignKey": "Foreign-key path validated by repository notebooks or semantic relationships.",
        "scdSemantics": "Implemented slowly changing dimension or current-state behavior.",
        "sourceColumn": "Relational source column represented by a property.",
        "dataClassification": "Repository classification vocabulary value.",
        "formulaReference": "Source-controlled formula or KPI definition artifact.",
        "schemaVersion": "Version of the schema contract.",
        "generatorVersion": "Version of the deterministic ontology generator.",
        "ambiguityNote": "Known source-model ambiguity that must not be silently strengthened.",
    }
    for name, comment in annotation_properties.items():
        graph.add((AO[name], RDF.type, OWL.AnnotationProperty))
        graph.add((AO[name], RDFS.label, Literal(words(name), lang="en")))
        graph.add((AO[name], RDFS.comment, Literal(comment, lang="en")))

    abstract_classes = [
        ("DomainEntity", None, "A physical, business, operational, or observational concept represented by the airport-operations domain."),
        ("PhysicalLocation", "DomainEntity", "A geographic or built-environment location in the airport hierarchy."),
        ("PhysicalAsset", "DomainEntity", "A physical item, equipment instance, meter, or aircraft instance."),
        ("BusinessEntity", "DomainEntity", "An organizational, commercial, workforce, route, or reference concept."),
        ("OperationalEvent", "DomainEntity", "A time-bounded synthetic operational occurrence or assignment."),
        ("Observation", "DomainEntity", "A synthetic measurement or status observation at a declared grain."),
        ("InformationArtifact", None, "A data, analytical, or governance artifact rather than a physical or operational entity."),
        ("AnalyticalRecord", "InformationArtifact", "A record in the conformed Warehouse or Gold analytical model."),
        ("DimensionRecord", "AnalyticalRecord", "A conformed descriptive record used to filter and group facts."),
        ("FactRecord", "AnalyticalRecord", "A record at a declared event, transaction, assignment, or observation grain."),
        ("BridgeRecord", "AnalyticalRecord", "An explicit relationship record connecting dimensions or facts."),
        ("AggregateProduct", "AnalyticalRecord", "A business-ready Gold aggregate or scorecard product."),
        ("MeasureDefinition", "InformationArtifact", "A governed KPI or measure definition with formula, unit, grain, and caveats."),
        ("MeasureObservation", "AnalyticalRecord", "A numeric observation of a governed measure for a subject and timestamp."),
        ("PublicReferenceAnchor", "DomainEntity", "A public geographic or industry reference identity used only as an anchor."),
    ]
    for name, parent, comment in abstract_classes:
        add_class(graph, name, parent, comment)

    for left, right in (
        ("PhysicalLocation", "PhysicalAsset"),
        ("PhysicalLocation", "BusinessEntity"),
        ("PhysicalLocation", "OperationalEvent"),
        ("PhysicalLocation", "Observation"),
        ("PhysicalAsset", "BusinessEntity"),
        ("PhysicalAsset", "OperationalEvent"),
        ("PhysicalAsset", "Observation"),
        ("BusinessEntity", "OperationalEvent"),
        ("BusinessEntity", "Observation"),
        ("OperationalEvent", "Observation"),
        ("DimensionRecord", "FactRecord"),
        ("DimensionRecord", "BridgeRecord"),
        ("FactRecord", "BridgeRecord"),
    ):
        graph.add((AO[left], OWL.disjointWith, AO[right]))

    domain_specs = [
        ("Airport", "PhysicalLocation", "A public geographic airport anchor participating in a fictional demonstration portfolio.", "dim_airport", "ops.vw_dim_airport", "one row per airport", "airport_id"),
        ("Terminal", "PhysicalLocation", "A synthetic passenger terminal contained by one airport.", "dim_terminal", "ops.vw_dim_terminal", "one row per terminal", "terminal_id"),
        ("Zone", "PhysicalLocation", "A synthetic indoor processing or secure-operations zone within a terminal.", "dim_zone", "ops.vw_dim_zone", "one row per indoor zone", "zone_id"),
        ("Checkpoint", "PhysicalLocation", "A synthetic passenger processing checkpoint within a zone.", "dim_checkpoint", "ops.vw_dim_checkpoint", "one row per passenger checkpoint", "checkpoint_id"),
        ("Gate", "PhysicalLocation", "A synthetic aircraft gate belonging to an airport terminal.", "dim_gate", "ops.vw_dim_gate", "one row per gate", "gate_id"),
        ("Stand", "PhysicalLocation", "A synthetic aircraft parking position served by a gate.", "dim_stand", "ops.vw_dim_stand", "one row per aircraft stand", "stand_id"),
        ("Asset", "PhysicalAsset", "A synthetic maintainable airport asset.", "dim_asset", "ops.vw_dim_asset", "one row per maintainable asset or energy meter", "asset_id"),
        ("MaintenanceAsset", "Asset", "A synthetic asset with maintenance class and service interval attributes.", "dim_asset", "ops.vw_dim_asset", "one row per maintainable asset", "asset_id"),
        ("EnergyMeter", "PhysicalAsset", "A synthetic meter that produces energy observations.", "dim_asset", "ops.vw_dim_asset", "one row per energy meter asset", "asset_id"),
        ("AircraftInstance", "PhysicalAsset", "A synthetic aircraft instance identified by a tail token.", "dim_aircraft_fleet", "ops.vw_dim_aircraft_fleet", "one row per synthetic aircraft instance", "aircraft_instance_id"),
        ("Organization", "BusinessEntity", "A fictional corporate headquarters or operating-region unit.", "dim_organization", "ops.vw_dim_organization", "one row per organization unit", "org_unit_id"),
        ("Airline", "BusinessEntity", "A public airline reference entity used by fictional schedules and routes.", "dim_airline", "ops.vw_dim_airline", "one row per airline", "airline_id"),
        ("AircraftType", "BusinessEntity", "A public aircraft-type reference with synthetic operating assumptions.", "dim_aircraft", "ops.vw_dim_aircraft", "one row per aircraft type", "aircraft_type_id"),
        ("Route", "BusinessEntity", "A fictional origin, destination, and airline service assumption.", "dim_route", "ops.vw_dim_route", "one row per fictional route", "route_id"),
        ("WorkTeam", "BusinessEntity", "A fictional airport service or maintenance team.", "dim_work_team", "ops.vw_dim_work_team", "one row per work team", "work_team_id"),
        ("ServiceTeam", "WorkTeam", "A fictional service-team concept retained from the base ontology.", "dim_service_team", "ops.vw_dim_service_team", "one row per airport service team", "team_id"),
        ("Skill", "BusinessEntity", "A synthetic workforce capability or certification assumption.", "dim_skill", None, "one row per skill", "skill_id"),
        ("Shift", "BusinessEntity", "A synthetic shift definition with UTC start and duration.", "dim_shift", None, "one row per shift", "shift_id"),
        ("PseudonymousWorkforceMember", "BusinessEntity", "A synthetic workforce token with no real identity fields.", "dim_employee", "ops.vw_dim_employee", "one row per pseudonymous workforce token", "employee_id"),
        ("RetailOutlet", "BusinessEntity", "A fictional concession outlet in an airport terminal.", "dim_retail_outlet", "ops.vw_dim_retail_outlet", "one row per retail outlet", "outlet_id"),
        ("RetailProduct", "BusinessEntity", "A fictional retail product with a synthetic unit-price proxy.", "dim_retail_product", "ops.vw_dim_retail_product", "one row per retail product", "product_id"),
        ("PseudonymousCustomer", "BusinessEntity", "A pseudonymous synthetic customer profile without direct identifiers.", "dim_customer", None, "one row per pseudonymous customer token", "customer_token"),
        ("PassengerCohort", "BusinessEntity", "An aggregate synthetic passenger segment; it is not a person identity.", "dim_customer_segment", None, "one row per customer segment", "customer_segment_id"),
        ("FlightOperation", "OperationalEvent", "A fictional scheduled flight movement represented by a turnaround fact.", "fact_flight_turnaround_events", "ops.vw_fact_turnaround", "one row per flight turnaround event", "flight_event_id"),
        ("Turnaround", "OperationalEvent", "The ground-operation interval associated one-to-one with a flight operation in the base fact.", "fact_flight_turnaround_events", "ops.vw_fact_turnaround", "one row per flight turnaround event", "flight_event_id"),
        ("AircraftRotation", "OperationalEvent", "A sequenced assignment of an aircraft instance to a flight.", "fact_aircraft_rotation", None, "one row per aircraft rotation sequence and flight", "rotation_id"),
        ("EmployeeRosterAssignment", "OperationalEvent", "A pseudonymous worker-to-team, shift, and location assignment.", "fact_employee_roster", "ops.vw_fact_employee_roster", "one row per worker and day assignment", "roster_assignment_id"),
        ("Booking", "OperationalEvent", "A synthetic passenger-token and flight booking record.", "fact_booking", "ops.vw_fact_booking", "one row per synthetic passenger and flight booking", "booking_id"),
        ("BoardingEvent", "OperationalEvent", "A synthetic booking and flight boarding outcome.", "fact_boarding_event", None, "one row per booking and flight boarding event", "boarding_event_id"),
        ("BaggageJourney", "OperationalEvent", "A synthetic checked-bag journey with load, reclaim, and exception outcome.", "fact_baggage_journey", "ops.vw_fact_baggage_journey", "one row per synthetic checked bag", "bag_token"),
        ("BaggageScan", "OperationalEvent", "A sequenced synthetic baggage scan event.", "fact_baggage_scan", None, "one row per synthetic baggage scan", "baggage_scan_id"),
        ("RampServiceTask", "OperationalEvent", "A deterministic ramp milestone task for a flight.", "fact_ramp_service_task", None, "one row per flight and ramp task", "ramp_task_id"),
        ("MaintenanceEvent", "OperationalEvent", "A synthetic maintenance observation associated with an airport asset type.", "fact_maintenance_events", "ops.vw_fact_maintenance_events", "one row per maintenance event", "maintenance_id"),
        ("MaintenanceWorkOrder", "OperationalEvent", "A synthetic analytical maintenance work order requiring governed approval metadata.", "fact_maintenance_work_order", None, "one row per maintenance work order", "work_order_id"),
        ("AssetInspection", "OperationalEvent", "A synthetic asset inspection with score, status, and follow-up flag.", "fact_asset_inspection", None, "one row per asset inspection", "inspection_id"),
        ("RetailTransaction", "OperationalEvent", "An aggregate synthetic outlet, product, and hour POS event.", "fact_retail_pos", "ops.vw_fact_retail_pos", "one row per outlet, product, and event hour", "pos_event_id"),
        ("TurnaroundPhase", "OperationalEvent", "One of five deterministic phase milestones within a flight turnaround.", "fact_turnaround_phase", "ops.vw_fact_turnaround_phase", "one row per flight and turnaround phase", "phase_event_id"),
        ("Recommendation", "OperationalEvent", "An advisory-only synthetic recommendation requiring human approval.", "fact_recommendation", None, "one row per recommendation", "recommendation_id"),
        ("PassengerFlowObservation", "Observation", "A PII-free aggregate checkpoint queue observation at 15-minute grain.", "fact_passenger_queue_metrics", "ops.vw_fact_passenger_flow", "one row per checkpoint and 15-minute interval", "queue_metric_id"),
        ("ZoneOccupancyObservation", "Observation", "A PII-free zone and checkpoint occupancy observation at 15-minute grain.", "fact_zone_occupancy", "ops.vw_fact_zone_occupancy", "one row per zone, checkpoint, and 15-minute interval", "zone_occupancy_id"),
        ("AssetStateObservation", "Observation", "A synthetic asset health observation at six-hour grain.", "fact_asset_state", "ops.vw_fact_asset_state", "one row per asset and six-hour interval", "asset_state_id"),
        ("EnergyObservation", "Observation", "A synthetic energy meter reading in kilowatt-hours.", "fact_energy_metering", "ops.vw_fact_energy_metering", "one row per energy meter reading", "meter_reading_id"),
        ("WeatherObservation", "Observation", "A synthetic hourly weather snapshot for an airport.", "fact_weather", "ops.vw_fact_weather", "one row per airport weather snapshot", "weather_id"),
        ("OperationalIncident", "OperationalEvent", "A synthetic operational incident; it is not a real safety or security record.", "fact_operational_incidents", "ops.vw_incident_details", "one row per operational incident", "incident_id"),
        ("RetailInventorySnapshot", "Observation", "A synthetic outlet and product inventory snapshot.", "fact_retail_inventory", None, "one row per outlet and product inventory snapshot", "inventory_snapshot_id"),
        ("CustomerExperienceObservation", "Observation", "An aggregate synthetic route and customer-segment experience observation.", "fact_customer_experience", "ops.vw_fact_customer_experience", "one row per flight and customer segment", "cx_event_id"),
    ]
    for name, parent, comment, table, view, grain, key in domain_specs:
        add_class(
            graph,
            name,
            parent,
            comment,
            source_table=table,
            source_view=view,
            grain=grain,
            primary_key=key,
            scd="current-state overwrite; no effective dating" if table and table.startswith("dim_") else None,
        )

    add_class(graph, "Aircraft", "AircraftType", "Compatibility name retained from the existing base ontology; the source grain is aircraft type.")
    graph.add((AO.Aircraft, OWL.equivalentClass, AO.AircraftType))
    graph.add((AO.Aircraft, OWL.deprecated, Literal(True)))
    add_class(graph, "Flight", "FlightOperation", "Compatibility name retained from the existing base ontology; the source grain is a flight turnaround event.")
    graph.add((AO.Flight, OWL.equivalentClass, AO.FlightOperation))
    graph.add((AO.Flight, OWL.deprecated, Literal(True)))
    add_class(graph, "AircraftFleet", "AircraftInstance", "Compatibility name retained from the existing enterprise ontology.")

    dimension_specs = [
        ("AirportDimensionRecord", "dim_airport", "ops.vw_dim_airport", "airport", "airport_id"),
        ("TerminalDimensionRecord", "dim_terminal", "ops.vw_dim_terminal", "terminal", "terminal_id"),
        ("ZoneDimensionRecord", "dim_zone", "ops.vw_dim_zone", "indoor zone", "zone_id"),
        ("CheckpointDimensionRecord", "dim_checkpoint", "ops.vw_dim_checkpoint", "passenger checkpoint", "checkpoint_id"),
        ("GateDimensionRecord", "dim_gate", "ops.vw_dim_gate", "gate", "gate_id"),
        ("StandDimensionRecord", "dim_stand", "ops.vw_dim_stand", "aircraft stand", "stand_id"),
        ("AssetDimensionRecord", "dim_asset", "ops.vw_dim_asset", "maintainable asset or meter", "asset_id"),
        ("LocationDimensionRecord", "dim_location", "ops.vw_dim_location", "physical or spatial location", "location_id"),
        ("DateDimensionRecord", "dim_date", "ops.vw_dim_date", "calendar date", "date_key"),
        ("TimeDimensionRecord", "dim_time", "ops.vw_dim_time", "hour from 0 through 23", "hour_key"),
        ("AirlineDimensionRecord", "dim_airline", "ops.vw_dim_airline", "airline reference", "airline_id"),
        ("AircraftTypeDimensionRecord", "dim_aircraft", "ops.vw_dim_aircraft", "aircraft type", "aircraft_type_id"),
        ("OrganizationDimensionRecord", "dim_organization", "ops.vw_dim_organization", "organization unit", "org_unit_id"),
        ("RouteDimensionRecord", "dim_route", "ops.vw_dim_route", "route", "route_id"),
        ("AircraftFleetDimensionRecord", "dim_aircraft_fleet", "ops.vw_dim_aircraft_fleet", "aircraft instance", "aircraft_instance_id"),
        ("WorkTeamDimensionRecord", "dim_work_team", "ops.vw_dim_work_team", "work team", "work_team_id"),
        ("SkillDimensionRecord", "dim_skill", None, "skill", "skill_id"),
        ("ShiftDimensionRecord", "dim_shift", None, "shift", "shift_id"),
        ("EmployeeDimensionRecord", "dim_employee", "ops.vw_dim_employee", "pseudonymous workforce token", "employee_id"),
        ("RetailOutletDimensionRecord", "dim_retail_outlet", "ops.vw_dim_retail_outlet", "retail outlet", "outlet_id"),
        ("RetailProductDimensionRecord", "dim_retail_product", "ops.vw_dim_retail_product", "retail product", "product_id"),
        ("CustomerDimensionRecord", "dim_customer", None, "pseudonymous customer token", "customer_token"),
        ("PassengerDimensionRecord", "dim_passenger", "ops.vw_dim_passenger", "pseudonymous passenger token", "passenger_token"),
        ("CustomerSegmentDimensionRecord", "dim_customer_segment", None, "customer segment", "customer_segment_id"),
    ]
    for name, table, view, grain, key in dimension_specs:
        add_class(
            graph,
            name,
            "DimensionRecord",
            f"Warehouse dimension record at one row per {grain}.",
            source_table=table,
            source_view=view,
            grain=f"one row per {grain}",
            primary_key=key,
            scd="current-state overwrite; no effective_from/effective_to columns",
        )

    bridge_specs = [
        ("AssetLocationBridgeRecord", "bridge_asset_location", "asset and location assignment", "asset_id + location_id", ("asset_id -> dim_asset.asset_id", "location_id -> dim_location.location_id"), "effective_from, effective_to, and is_current are implemented; generator currently emits only current rows"),
        ("GateStandBridgeRecord", "bridge_gate_stand", "gate and stand assignment", "gate_id + stand_id", ("gate_id -> dim_gate.gate_id", "stand_id -> dim_stand.stand_id"), "effective_from and is_current are implemented; no effective_to column"),
        ("FlightRouteBridgeRecord", "bridge_flight_route", "flight and route assignment", "flight_event_id", ("route_id -> dim_route.route_id", "aircraft_instance_id -> dim_aircraft_fleet.aircraft_instance_id"), "current assignment only; no effective dates"),
        ("EmployeeSkillBridgeRecord", "bridge_employee_skill", "employee and skill capability", "employee_skill_id", ("employee_id -> dim_employee.employee_id", "skill_id -> dim_skill.skill_id"), "current assignment only; no effective dates"),
    ]
    for name, table, grain, key, foreign_keys, scd in bridge_specs:
        add_class(
            graph,
            name,
            "BridgeRecord",
            f"Warehouse bridge record at one row per {grain}.",
            source_table=table,
            grain=f"one row per {grain}",
            primary_key=key,
            foreign_keys=foreign_keys,
            scd=scd,
        )

    fact_specs = [
        ("FlightTurnaroundFactRecord", "fact_flight_turnaround_events", "ops.vw_fact_turnaround", "flight turnaround event", "flight_event_id", ("airport_id -> dim_airport.airport_id", "gate_id -> dim_gate.gate_id", "airline_id -> dim_airline.airline_id", "aircraft_type_id -> dim_aircraft.aircraft_type_id", "date_key -> dim_date.date_key")),
        ("PassengerQueueFactRecord", "fact_passenger_queue_metrics", "ops.vw_fact_passenger_flow", "checkpoint and 15-minute observation", "queue_metric_id", ("airport_id -> dim_airport.airport_id", "date_key -> dim_date.date_key")),
        ("ZoneOccupancyFactRecord", "fact_zone_occupancy", "ops.vw_fact_zone_occupancy", "zone, checkpoint, and 15-minute observation", "zone_occupancy_id", ("zone_id -> dim_zone.zone_id", "checkpoint_id -> dim_checkpoint.checkpoint_id")),
        ("AssetStateFactRecord", "fact_asset_state", "ops.vw_fact_asset_state", "asset and six-hour observation", "asset_state_id", ("asset_id -> dim_asset.asset_id",)),
        ("EnergyMeteringFactRecord", "fact_energy_metering", "ops.vw_fact_energy_metering", "energy meter reading", "meter_reading_id", ("gate_id -> dim_gate.gate_id",)),
        ("MaintenanceEventFactRecord", "fact_maintenance_events", "ops.vw_fact_maintenance_events", "maintenance event", "maintenance_id", ("airport_id -> dim_airport.airport_id", "gate_id -> dim_gate.gate_id")),
        ("OperationalIncidentFactRecord", "fact_operational_incidents", "ops.vw_incident_details", "operational incident", "incident_id", ("airport_id -> dim_airport.airport_id", "gate_id -> dim_gate.gate_id")),
        ("WeatherFactRecord", "fact_weather", "ops.vw_fact_weather", "airport weather snapshot", "weather_id", ("airport_id -> dim_airport.airport_id",)),
        ("FlightLegFactRecord", "fact_flight_leg", None, "flight leg", "leg_id", ("flight_event_id -> fact_flight_turnaround_events.flight_event_id", "route_id -> dim_route.route_id")),
        ("AircraftRotationFactRecord", "fact_aircraft_rotation", None, "aircraft rotation sequence and flight", "rotation_id", ("aircraft_instance_id -> dim_aircraft_fleet.aircraft_instance_id", "flight_event_id -> fact_flight_turnaround_events.flight_event_id")),
        ("EmployeeRosterFactRecord", "fact_employee_roster", "ops.vw_fact_employee_roster", "worker and day assignment", "roster_assignment_id", ("employee_id -> dim_employee.employee_id", "work_team_id -> dim_work_team.work_team_id", "shift_id -> dim_shift.shift_id")),
        ("BookingFactRecord", "fact_booking", "ops.vw_fact_booking", "passenger and flight booking", "booking_id", ("passenger_token -> dim_passenger.passenger_token", "route_id -> dim_route.route_id")),
        ("BoardingEventFactRecord", "fact_boarding_event", None, "booking and flight boarding event", "boarding_event_id", ("booking_id -> fact_booking.booking_id", "flight_event_id -> fact_flight_turnaround_events.flight_event_id")),
        ("BaggageJourneyFactRecord", "fact_baggage_journey", "ops.vw_fact_baggage_journey", "synthetic checked bag", "bag_token", ("booking_id -> fact_booking.booking_id",)),
        ("BaggageScanFactRecord", "fact_baggage_scan", None, "synthetic baggage scan", "baggage_scan_id", ("bag_token -> fact_baggage_journey.bag_token",)),
        ("RampServiceTaskFactRecord", "fact_ramp_service_task", None, "flight and ramp task", "ramp_task_id", ("flight_event_id -> fact_flight_turnaround_events.flight_event_id",)),
        ("MaintenanceWorkOrderFactRecord", "fact_maintenance_work_order", None, "maintenance work order", "work_order_id", ("maintenance_id -> fact_maintenance_events.maintenance_id",)),
        ("AssetInspectionFactRecord", "fact_asset_inspection", None, "asset inspection", "inspection_id", ("asset_id -> dim_asset.asset_id",)),
        ("RetailTransactionFactRecord", "fact_retail_pos", "ops.vw_fact_retail_pos", "outlet, product, and event hour", "pos_event_id", ("outlet_id -> dim_retail_outlet.outlet_id", "product_id -> dim_retail_product.product_id")),
        ("RetailInventoryFactRecord", "fact_retail_inventory", None, "outlet and product inventory snapshot", "inventory_snapshot_id", ("outlet_id -> dim_retail_outlet.outlet_id", "product_id -> dim_retail_product.product_id")),
        ("TurnaroundPhaseFactRecord", "fact_turnaround_phase", "ops.vw_fact_turnaround_phase", "flight and turnaround phase", "phase_event_id", ("flight_event_id -> fact_flight_turnaround_events.flight_event_id",)),
        ("CustomerExperienceFactRecord", "fact_customer_experience", "ops.vw_fact_customer_experience", "flight and customer segment", "cx_event_id", ("route_id -> dim_route.route_id",)),
        ("RecommendationFactRecord", "fact_recommendation", None, "advisory recommendation", "recommendation_id", ("airport_id -> dim_airport.airport_id",)),
    ]
    for name, table, view, grain, key, foreign_keys in fact_specs:
        add_class(
            graph,
            name,
            "FactRecord",
            f"Warehouse fact record at one row per {grain}.",
            source_table=table,
            source_view=view,
            grain=f"one row per {grain}",
            primary_key=key,
            foreign_keys=foreign_keys,
        )

    aggregate_specs = [
        ("AirportOperationalHealth", "gold_airport_operational_health", "ops.vw_airport_performance", "airport"),
        ("TerminalFlowSummary", "gold_terminal_flow_summary", "ops.vw_terminal_performance", "airport, terminal, and hour"),
        ("GateTurnaroundPerformance", "gold_gate_turnaround_performance", "ops.vw_gate_turnaround_performance", "gate and stand"),
        ("AssetReliability", "gold_asset_reliability", "ops.vw_asset_reliability", "asset"),
        ("EnergyEfficiency", "gold_energy_efficiency", "ops.vw_energy_efficiency", "gate"),
        ("SpatialOperationalStatus", "gold_spatial_operational_status", "ops.vw_spatial_operational_context", "zone"),
        ("ExecutiveScorecard", "gold_executive_scorecard", "ops.vw_executive_scorecard", "airport"),
        ("ITServiceHealth", "gold_it_service_health", "ops.vw_it_service_health", "data product"),
        ("AirlineRoutePerformance", "gold_airline_route_performance", "ops.vw_airline_route_performance", "airline and route"),
        ("BaggagePerformance", "gold_baggage_performance", "ops.vw_baggage_performance", "origin and destination"),
        ("WorkforceCoverage", "gold_workforce_coverage", "ops.vw_workforce_coverage", "team and shift"),
        ("RetailPerformance", "gold_retail_performance", "ops.vw_retail_performance", "retail outlet"),
        ("CustomerExperience", "gold_customer_experience", "ops.vw_customer_experience", "route and customer segment"),
        ("TurnaroundPhasePerformance", "gold_turnaround_phase_performance", "ops.vw_turnaround_phase_performance", "gate and phase"),
        ("PersonaScorecard", "gold_persona_scorecard", "ops.vw_persona_scorecard", "airport and persona"),
        ("FlightOperationsKPI", "gold_flight_operations_kpi", "ops.vw_flight_operations_kpi", "airport and day"),
        ("PassengerFlowKPI", "gold_passenger_flow_kpi", "ops.vw_passenger_flow_kpi", "airport and day"),
        ("BaggageKPI", "gold_baggage_kpi", "ops.vw_baggage_kpi", "airport and day"),
        ("WorkforceKPI", "gold_workforce_kpi", "ops.vw_workforce_kpi", "airport and day"),
        ("MaintenanceKPI", "gold_maintenance_kpi", "ops.vw_maintenance_kpi", "airport and day"),
        ("EnergySustainabilityKPI", "gold_energy_sustainability_kpi", "ops.vw_energy_sustainability_kpi", "airport and day"),
        ("CommercialKPI", "gold_commercial_kpi", "ops.vw_commercial_kpi", "airport and day"),
        ("IncidentCustomerKPI", "gold_incident_customer_kpi", "ops.vw_incident_customer_kpi", "airport and day"),
        ("AircraftRotationKPI", "gold_aircraft_rotation_kpi", "ops.vw_aircraft_rotation_kpi", "airport and day"),
        ("RetailInventoryKPI", "gold_retail_inventory_kpi", "ops.vw_retail_inventory_kpi", "airport and day"),
        ("KPICatalog", "gold_kpi_catalog", "ops.vw_kpi_catalog", "KPI"),
    ]
    for name, table, view, grain in aggregate_specs:
        add_class(
            graph,
            name,
            "AggregateProduct",
            f"Gold analytical product at one row per {grain}.",
            source_table=table,
            source_view=view,
            grain=f"one row per {grain}",
        )

    add_class(graph, "BookingPerformance", "AggregateProduct", "Aggregate synthetic booking and ticket-revenue proxy performance.", source_table="gold_airline_route_performance", source_view="ops.vw_airline_route_performance", grain="one row per airline and route")
    add_class(graph, "RetailInventory", "RetailInventoryKPI", "Compatibility concept retained from the enterprise ontology for aggregate retail inventory performance.")
    add_class(graph, "KPI", "MeasureDefinition", "Compatibility concept retained from the base ontology for a governed semantic measure.", source_table="gold_kpi_catalog", source_view="ops.vw_kpi_catalog", grain="one row per KPI")

    add_object_property(graph, "contains", "contains", "Transitive physical containment relation.", "PhysicalLocation", "DomainEntity", inverse="containedIn", transitive=True)
    add_object_property(graph, "containedIn", "contained in", "Inverse of physical containment.", "DomainEntity", "PhysicalLocation", inverse="contains", transitive=True)
    object_properties = [
        ("hasTerminal", "has terminal", "Airport contains terminal.", "Airport", "Terminal", "terminalOfAirport", "contains", False),
        ("terminalOfAirport", "terminal of airport", "Terminal belongs to one airport.", "Terminal", "Airport", "hasTerminal", "containedIn", True),
        ("hasZone", "has zone", "Terminal contains zone.", "Terminal", "Zone", "zoneOfTerminal", "contains", False),
        ("zoneOfTerminal", "zone of terminal", "Zone belongs to one terminal.", "Zone", "Terminal", "hasZone", "containedIn", True),
        ("hasCheckpoint", "has checkpoint", "Zone contains checkpoint.", "Zone", "Checkpoint", "checkpointOfZone", "contains", False),
        ("checkpointOfZone", "checkpoint of zone", "Checkpoint belongs to one zone.", "Checkpoint", "Zone", "hasCheckpoint", "containedIn", True),
        ("hasGate", "has gate", "Terminal contains gate.", "Terminal", "Gate", "gateOfTerminal", "contains", False),
        ("gateOfTerminal", "gate of terminal", "Gate belongs to one terminal.", "Gate", "Terminal", "hasGate", "containedIn", True),
        ("servesStand", "serves stand", "Gate serves an adjacent stand.", "Gate", "Stand", "standServedByGate", None, False),
        ("standServedByGate", "stand served by gate", "Stand is served by one gate in the current bridge.", "Stand", "Gate", "servesStand", None, True),
        ("containsAsset", "contains asset", "Zone contains an asset.", "Zone", "Asset", "assetLocatedInZone", "contains", False),
        ("assetLocatedInZone", "asset located in zone", "Asset is assigned to a zone in the generated spatial model.", "Asset", "Zone", "containsAsset", "containedIn", True),
        ("hasPassengerFlowObservation", "has passenger flow observation", "Zone has a PII-free passenger-flow observation.", "Zone", "PassengerFlowObservation", "passengerFlowObservedInZone", None, False),
        ("passengerFlowObservedInZone", "passenger flow observed in zone", "Passenger-flow observation occurs in one zone.", "PassengerFlowObservation", "Zone", "hasPassengerFlowObservation", None, True),
        ("monitoredBy", "monitored by", "Asset is monitored by an energy meter.", "Asset", "EnergyMeter", "monitorsAsset", None, False),
        ("monitorsAsset", "monitors asset", "Energy meter monitors an asset.", "EnergyMeter", "Asset", "monitoredBy", None, False),
        ("hasWorkOrder", "has work order", "Asset has an analytical maintenance work order.", "Asset", "MaintenanceWorkOrder", "workOrderForAsset", None, False),
        ("workOrderForAsset", "work order for asset", "Maintenance work order concerns an asset.", "MaintenanceWorkOrder", "Asset", "hasWorkOrder", None, True),
        ("servesFlight", "serves flight", "Gate serves a flight operation.", "Gate", "FlightOperation", "servedAtGate", None, False),
        ("servedAtGate", "served at gate", "Flight operation occurs at one gate.", "FlightOperation", "Gate", "servesFlight", None, True),
        ("usesAircraftType", "uses aircraft type", "Flight operation uses one aircraft type.", "FlightOperation", "AircraftType", "aircraftTypeUsedByFlight", None, True),
        ("aircraftTypeUsedByFlight", "aircraft type used by flight", "Aircraft type is used by a flight.", "AircraftType", "FlightOperation", "usesAircraftType", None, False),
        ("flightOperatedByAirline", "flight operated by airline", "Flight operation is operated by one airline reference.", "FlightOperation", "Airline", "airlineOperatesFlight", None, True),
        ("airlineOperatesFlight", "airline operates flight", "Airline operates a fictional flight.", "Airline", "FlightOperation", "flightOperatedByAirline", None, False),
        ("routeOperatedByAirline", "route operated by airline", "Route service assumption names one airline.", "Route", "Airline", "airlineOperatesRoute", None, True),
        ("airlineOperatesRoute", "airline operates route", "Airline is assigned a fictional route.", "Airline", "Route", "routeOperatedByAirline", None, False),
        ("originAirport", "origin airport", "Route originates at one airport.", "Route", "Airport", "originForRoute", None, True),
        ("originForRoute", "origin for route", "Airport is the origin of a route.", "Airport", "Route", "originAirport", None, False),
        ("destinationAirport", "destination airport", "Route terminates at one airport.", "Route", "Airport", "destinationForRoute", None, True),
        ("destinationForRoute", "destination for route", "Airport is the destination of a route.", "Airport", "Route", "destinationAirport", None, False),
        ("flightOnRoute", "flight on route", "Flight operation is assigned to a route by bridge_flight_route.", "FlightOperation", "Route", "routeHasFlight", None, True),
        ("routeHasFlight", "route has flight", "Route has a fictional flight operation.", "Route", "FlightOperation", "flightOnRoute", None, False),
        ("hasTurnaround", "has turnaround", "Flight has one turnaround interval in the base fact.", "FlightOperation", "Turnaround", "turnaroundOfFlight", None, True),
        ("turnaroundOfFlight", "turnaround of flight", "Turnaround corresponds to one flight operation.", "Turnaround", "FlightOperation", "hasTurnaround", None, True),
        ("rotationUsesAircraft", "rotation uses aircraft", "Rotation assigns one aircraft instance.", "AircraftRotation", "AircraftInstance", "aircraftHasRotation", None, True),
        ("aircraftHasRotation", "aircraft has rotation", "Aircraft instance participates in a rotation sequence.", "AircraftInstance", "AircraftRotation", "rotationUsesAircraft", None, False),
        ("rotationForFlight", "rotation for flight", "Rotation assigns one flight operation.", "AircraftRotation", "FlightOperation", "flightHasRotation", None, True),
        ("flightHasRotation", "flight has rotation", "Flight operation has an aircraft rotation assignment.", "FlightOperation", "AircraftRotation", "rotationForFlight", None, False),
        ("affectsAsset", "affects asset", "Operational incident affects a synthetic asset.", "OperationalIncident", "Asset", "affectedByIncident", None, False),
        ("affectedByIncident", "affected by incident", "Asset is affected by an operational incident.", "Asset", "OperationalIncident", "affectsAsset", None, False),
        ("representsEntity", "represents entity", "Dimension record represents a domain entity.", "DimensionRecord", "DomainEntity", "hasDimensionRecord", None, True),
        ("hasDimensionRecord", "has dimension record", "Domain entity is represented by a dimension record.", "DomainEntity", "DimensionRecord", "representsEntity", None, False),
        ("representsEvent", "represents event", "Fact record represents an event or observation.", "FactRecord", "DomainEntity", "hasFactRecord", None, True),
        ("hasFactRecord", "has fact record", "Domain event or observation is represented by a fact record.", "DomainEntity", "FactRecord", "representsEvent", None, False),
        ("hasDimensionMember", "has dimension member", "Fact record references a dimension record.", "FactRecord", "DimensionRecord", "dimensionMemberOfFact", None, False),
        ("dimensionMemberOfFact", "dimension member of fact", "Dimension record is referenced by a fact record.", "DimensionRecord", "FactRecord", "hasDimensionMember", None, False),
        ("observedFor", "observed for", "Measure observation applies to a domain entity or analytical record.", "MeasureObservation", "DomainEntity", "hasMeasureObservation", None, True),
        ("hasMeasureObservation", "has measure observation", "Domain entity has a measure observation.", "DomainEntity", "MeasureObservation", "observedFor", None, False),
        ("observesMeasure", "observes measure", "Measure observation instantiates a governed measure definition.", "MeasureObservation", "MeasureDefinition", "hasObservation", None, True),
        ("hasObservation", "has observation", "Measure definition has observations.", "MeasureDefinition", "MeasureObservation", "observesMeasure", None, False),
    ]
    for name, label, comment, domain, range_name, inverse, parent, functional in object_properties:
        add_object_property(graph, name, label, comment, domain, range_name, inverse=inverse, parent=parent, functional=functional)

    data_properties = [
        ("identifier", "identifier", "Stable source-system or ontology identifier.", "DomainEntity", XSD.string, None),
        ("recordIdentifier", "record identifier", "Primary/business key value for an analytical record.", "AnalyticalRecord", XSD.string, None),
        ("airportId", "airport identifier", "Value of airport_id.", "Airport", XSD.string, "identifier"),
        ("terminalId", "terminal identifier", "Value of terminal_id.", "Terminal", XSD.string, "identifier"),
        ("zoneId", "zone identifier", "Value of zone_id.", "Zone", XSD.string, "identifier"),
        ("checkpointId", "checkpoint identifier", "Value of checkpoint_id.", "Checkpoint", XSD.string, "identifier"),
        ("gateId", "gate identifier", "Value of gate_id.", "Gate", XSD.string, "identifier"),
        ("standId", "stand identifier", "Value of stand_id.", "Stand", XSD.string, "identifier"),
        ("assetId", "asset identifier", "Value of asset_id.", "PhysicalAsset", XSD.string, "identifier"),
        ("airlineId", "airline identifier", "Value of airline_id.", "Airline", XSD.string, "identifier"),
        ("aircraftTypeId", "aircraft type identifier", "Value of aircraft_type_id.", "AircraftType", XSD.string, "identifier"),
        ("routeId", "route identifier", "Value of route_id.", "Route", XSD.string, "identifier"),
        ("flightEventId", "flight event identifier", "Value of flight_event_id.", "FlightOperation", XSD.string, "identifier"),
        ("workOrderId", "work order identifier", "Value of work_order_id.", "MaintenanceWorkOrder", XSD.string, "identifier"),
        ("incidentId", "incident identifier", "Value of incident_id.", "OperationalIncident", XSD.string, "identifier"),
        ("queueObservationId", "queue observation identifier", "Value of queue_metric_id or DTDL queueId.", "PassengerFlowObservation", XSD.string, "identifier"),
        ("isSynthetic", "is synthetic", "True for generated operational/master records; false for public reference anchors.", "DomainEntity", XSD.boolean, None),
        ("iataCode", "IATA code", "Public IATA reference code used by airports and airlines.", "DomainEntity", XSD.string, None),
        ("icaoCode", "ICAO code", "Public ICAO reference code used by airports and airlines.", "DomainEntity", XSD.string, None),
        ("terminalCode", "terminal code", "Synthetic terminal code.", "Terminal", XSD.string, None),
        ("zoneType", "zone type", "Synthetic zone category.", "Zone", XSD.string, None),
        ("checkpointCode", "checkpoint code", "Synthetic checkpoint code.", "Checkpoint", XSD.string, None),
        ("gateCode", "gate code", "Synthetic gate code.", "Gate", XSD.string, None),
        ("assetType", "asset type", "Synthetic asset type.", "PhysicalAsset", XSD.string, None),
        ("criticality", "criticality", "Narrative synthetic criticality classification.", "PhysicalAsset", XSD.string, None),
        ("status", "status", "Controlled status value at the source grain.", "DomainEntity", XSD.string, None),
        ("severity", "severity", "Controlled incident or maintenance severity value.", "OperationalEvent", XSD.string, None),
        ("latitude", "latitude", "WGS84 latitude.", "PhysicalLocation", XSD.decimal, None),
        ("longitude", "longitude", "WGS84 longitude.", "PhysicalLocation", XSD.decimal, None),
        ("spatialReference", "spatial reference", "GeoJSON, map-feature, or WKT reference used by the spatial model.", "PhysicalLocation", XSD.string, None),
        ("twinIdentifier", "digital twin identifier", "Azure Digital Twins sample identifier.", "DomainEntity", XSD.string, None),
        ("eventTime", "event time", "UTC event or observation timestamp.", "DomainEntity", XSD.dateTime, None),
        ("scheduledArrival", "scheduled arrival", "Scheduled UTC arrival timestamp.", "FlightOperation", XSD.dateTime, None),
        ("actualArrival", "actual arrival", "Actual UTC arrival timestamp.", "FlightOperation", XSD.dateTime, None),
        ("scheduledDeparture", "scheduled departure", "Scheduled UTC departure timestamp.", "FlightOperation", XSD.dateTime, None),
        ("actualDeparture", "actual departure", "Actual UTC departure timestamp.", "FlightOperation", XSD.dateTime, None),
        ("turnaroundMinutes", "turnaround minutes", "Derived turnaround interval in minutes.", "Turnaround", XSD.decimal, None),
        ("departureDelayMinutes", "departure delay minutes", "Derived departure delay in minutes.", "FlightOperation", XSD.decimal, None),
        ("passengerCount", "passenger count", "Synthetic aggregate passenger count.", "DomainEntity", XSD.integer, None),
        ("waitTimeMinutes", "wait time minutes", "Synthetic queue wait in minutes.", "PassengerFlowObservation", XSD.decimal, None),
        ("occupancyCount", "occupancy count", "PII-free aggregate occupancy count.", "ZoneOccupancyObservation", XSD.integer, None),
        ("throughputPassengerCount", "throughput passenger count", "PII-free aggregate passenger throughput.", "Observation", XSD.integer, None),
        ("availabilityPercentage", "availability percentage", "Synthetic asset availability percentage.", "AssetStateObservation", XSD.decimal, None),
        ("anomalyFlag", "anomaly flag", "Synthetic anomaly indicator.", "Observation", XSD.boolean, None),
        ("energyKwh", "energy in kilowatt-hours", "Synthetic energy reading in kWh.", "EnergyObservation", XSD.decimal, None),
        ("numericValue", "numeric value", "Numeric measure observation value.", "MeasureObservation", XSD.decimal, None),
        ("unitCode", "unit code", "Stable display unit such as min, %, count, or kWh.", "MeasureDefinition", XSD.string, None),
        ("formulaText", "formula text", "Source-controlled descriptive formula; DAX remains authoritative for semantic measures.", "MeasureDefinition", XSD.string, None),
        ("grainText", "grain text", "Declared aggregation grain.", "MeasureDefinition", XSD.string, None),
        ("valueType", "value type", "Actual, target, benchmark, forecast, or proxy semantic.", "MeasureObservation", XSD.string, None),
        ("observationTimestamp", "observation timestamp", "Fixed demo as-of timestamp for an analytical observation.", "MeasureObservation", XSD.dateTime, None),
        ("effectiveFrom", "effective from", "Start of an effective bridge assignment.", "BridgeRecord", XSD.dateTime, None),
        ("effectiveTo", "effective to", "Optional end of an effective bridge assignment.", "BridgeRecord", XSD.dateTime, None),
        ("isCurrent", "is current", "Current bridge assignment indicator.", "BridgeRecord", XSD.boolean, None),
        ("advisoryOnly", "advisory only", "True when a recommendation cannot control an operational system.", "Recommendation", XSD.boolean, None),
        ("humanApprovalRequired", "human approval required", "True when a recommendation requires human approval.", "Recommendation", XSD.boolean, None),
    ]
    for name, label, comment, domain, datatype, parent in data_properties:
        add_datatype_property(graph, name, label, comment, domain, datatype, parent=parent, functional=name.endswith("Id") or name in {"recordIdentifier"})

    for property_name, column_name in {
        "airportId": "airport_id", "terminalId": "terminal_id", "zoneId": "zone_id",
        "checkpointId": "checkpoint_id", "gateId": "gate_id", "standId": "stand_id",
        "assetId": "asset_id", "airlineId": "airline_id", "aircraftTypeId": "aircraft_type_id",
        "routeId": "route_id", "flightEventId": "flight_event_id", "workOrderId": "work_order_id",
        "incidentId": "incident_id", "turnaroundMinutes": "turnaround_minutes",
        "departureDelayMinutes": "departure_delay_minutes", "waitTimeMinutes": "wait_time_min",
        "energyKwh": "kwh", "effectiveFrom": "effective_from", "effectiveTo": "effective_to",
        "isCurrent": "is_current",
    }.items():
        graph.add((AO[property_name], AO.sourceColumn, Literal(column_name)))

    add_min_cardinality(graph, "Airport", "hasTerminal", "Terminal", 1)
    add_exact_cardinality(graph, "Terminal", "terminalOfAirport", "Airport")
    add_exact_cardinality(graph, "Zone", "zoneOfTerminal", "Terminal")
    add_exact_cardinality(graph, "Checkpoint", "checkpointOfZone", "Zone")
    add_exact_cardinality(graph, "Gate", "gateOfTerminal", "Terminal")
    add_exact_cardinality(graph, "Stand", "standServedByGate", "Gate")
    add_exact_cardinality(graph, "Asset", "assetLocatedInZone", "Zone")
    add_exact_cardinality(graph, "Route", "originAirport", "Airport")
    add_exact_cardinality(graph, "Route", "destinationAirport", "Airport")
    add_exact_cardinality(graph, "Route", "routeOperatedByAirline", "Airline")
    add_exact_cardinality(graph, "FlightOperation", "servedAtGate", "Gate")
    add_exact_cardinality(graph, "FlightOperation", "usesAircraftType", "AircraftType")
    add_exact_cardinality(graph, "FlightOperation", "flightOperatedByAirline", "Airline")
    add_exact_cardinality(graph, "FlightOperation", "flightOnRoute", "Route")
    add_exact_cardinality(graph, "FlightOperation", "hasTurnaround", "Turnaround")
    add_exact_cardinality(graph, "Turnaround", "turnaroundOfFlight", "FlightOperation")
    add_exact_cardinality(graph, "AircraftRotation", "rotationUsesAircraft", "AircraftInstance")
    add_exact_cardinality(graph, "AircraftRotation", "rotationForFlight", "FlightOperation")

    graph.add((AO.Asset, AO.ambiguityNote, Literal("dim_asset contains zone_id, gate_id, terminal_id, and airport_id; bridge_asset_location is the effective-dated spatial assignment authority.")))
    graph.add((AO.OperationalIncident, AO.ambiguityNote, Literal("delay_reason is a primary narrative cause; the source does not implement an atomic many-cause delay bridge.")))
    graph.add((AO.MeasureDefinition, AO.ambiguityNote, Literal("semantic-model/measures.dax is authoritative; gold_kpi_catalog formula text is descriptive metadata.")))
    graph.add((AO.PassengerCohort, AO.ambiguityNote, Literal("Passenger and customer tokens exist in restricted facts, but agent-facing ontology mappings expose aggregate cohorts only.")))

    return graph


def add_shape_property(
    graph: Graph,
    shape_name: str,
    property_name: str,
    *,
    min_count: int | None = None,
    max_count: int | None = None,
    datatype: URIRef | None = None,
    class_name: str | None = None,
    minimum: Decimal | None = None,
    maximum: Decimal | None = None,
) -> None:
    property_shape = BNode(f"shape-{shape_name}-{property_name}")
    graph.add((AO[f"{shape_name}Shape"], SH.property, property_shape))
    graph.add((property_shape, SH.path, AO[property_name]))
    if min_count is not None:
        graph.add((property_shape, SH.minCount, Literal(min_count)))
    if max_count is not None:
        graph.add((property_shape, SH.maxCount, Literal(max_count)))
    if datatype:
        graph.add((property_shape, SH.datatype, datatype))
    if class_name:
        graph.add((property_shape, SH["class"], AO[class_name]))
    if minimum is not None:
        graph.add((property_shape, SH.minInclusive, Literal(minimum)))
    if maximum is not None:
        graph.add((property_shape, SH.maxInclusive, Literal(maximum)))


def add_unique_identifier_constraint(graph: Graph, shape_name: str, property_name: str) -> None:
    constraint = BNode(f"constraint-{shape_name}-{property_name}-unique")
    graph.add((AO[f"{shape_name}Shape"], SH.sparql, constraint))
    graph.add((constraint, SH.message, Literal(f"{property_name} must be unique within {shape_name}.")))
    graph.add((constraint, SH.select, Literal(
        f"SELECT $this WHERE {{ $this <{AO[property_name]}> ?value . "
        f"?other a <{AO[shape_name]}> ; <{AO[property_name]}> ?value . FILTER (?other != $this) }}"
    )))


def build_shapes_graph() -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/shapes"), RDF.type, OWL.Ontology))
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/shapes"), DCTERMS.title, Literal("Airport Operations SHACL Shapes", lang="en")))
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/shapes"), OWL.versionInfo, Literal(VERSION)))

    shapes = {
        "Airport": "Public airport anchor.", "Terminal": "Synthetic terminal.", "Zone": "Synthetic zone.",
        "Checkpoint": "Synthetic checkpoint.", "Gate": "Synthetic gate.", "Stand": "Synthetic stand.",
        "Asset": "Synthetic airport asset.", "Route": "Fictional route.", "FlightOperation": "Fictional flight operation.",
        "OperationalIncident": "Synthetic operational incident.", "MeasureObservation": "Governed measure observation.",
    }
    for name, comment in shapes.items():
        shape = AO[f"{name}Shape"]
        graph.add((shape, RDF.type, SH.NodeShape))
        graph.add((shape, SH.targetClass, AO[name]))
        graph.add((shape, RDFS.label, Literal(f"{words(name)} shape", lang="en")))
        graph.add((shape, RDFS.comment, Literal(comment, lang="en")))

    for shape_name, property_name in (
        ("Airport", "airportId"), ("Terminal", "terminalId"), ("Zone", "zoneId"),
        ("Checkpoint", "checkpointId"), ("Gate", "gateId"), ("Stand", "standId"),
        ("Asset", "assetId"), ("Route", "routeId"), ("FlightOperation", "flightEventId"),
        ("OperationalIncident", "incidentId"),
    ):
        add_shape_property(graph, shape_name, property_name, min_count=1, max_count=1, datatype=XSD.string)
        add_unique_identifier_constraint(graph, shape_name, property_name)

    for shape_name in ("Airport", "Terminal", "Zone", "Checkpoint", "Gate", "Stand", "Asset", "Route", "FlightOperation", "OperationalIncident"):
        add_shape_property(graph, shape_name, "isSynthetic", min_count=1, max_count=1, datatype=XSD.boolean)

    add_shape_property(graph, "Airport", "latitude", max_count=1, datatype=XSD.decimal, minimum=Decimal("-90"), maximum=Decimal("90"))
    add_shape_property(graph, "Airport", "longitude", max_count=1, datatype=XSD.decimal, minimum=Decimal("-180"), maximum=Decimal("180"))
    add_shape_property(graph, "Terminal", "terminalOfAirport", min_count=1, max_count=1, class_name="Airport")
    add_shape_property(graph, "Zone", "zoneOfTerminal", min_count=1, max_count=1, class_name="Terminal")
    add_shape_property(graph, "Checkpoint", "checkpointOfZone", min_count=1, max_count=1, class_name="Zone")
    add_shape_property(graph, "Gate", "gateOfTerminal", min_count=1, max_count=1, class_name="Terminal")
    add_shape_property(graph, "Stand", "standServedByGate", min_count=1, max_count=1, class_name="Gate")
    add_shape_property(graph, "Route", "originAirport", min_count=1, max_count=1, class_name="Airport")
    add_shape_property(graph, "Route", "destinationAirport", min_count=1, max_count=1, class_name="Airport")
    add_shape_property(graph, "Route", "routeOperatedByAirline", min_count=1, max_count=1, class_name="Airline")
    add_shape_property(graph, "FlightOperation", "servedAtGate", min_count=1, max_count=1, class_name="Gate")
    add_shape_property(graph, "FlightOperation", "usesAircraftType", min_count=1, max_count=1, class_name="AircraftType")
    add_shape_property(graph, "FlightOperation", "flightOperatedByAirline", min_count=1, max_count=1, class_name="Airline")
    add_shape_property(graph, "FlightOperation", "flightOnRoute", min_count=1, max_count=1, class_name="Route")
    add_shape_property(graph, "FlightOperation", "hasTurnaround", min_count=1, max_count=1, class_name="Turnaround")
    add_shape_property(graph, "MeasureObservation", "numericValue", min_count=1, max_count=1, datatype=XSD.decimal)
    add_shape_property(graph, "MeasureObservation", "observesMeasure", min_count=1, max_count=1, class_name="MeasureDefinition")
    add_shape_property(graph, "MeasureObservation", "observedFor", min_count=1, max_count=1, class_name="DomainEntity")
    add_shape_property(graph, "MeasureObservation", "observationTimestamp", min_count=1, max_count=1, datatype=XSD.dateTime)
    return graph


def resource(identifier: str) -> URIRef:
    return RES[quote(identifier, safe="")]


def add_inverse_pair(graph: Graph, source: URIRef, predicate: URIRef, target: URIRef, inverse: URIRef) -> None:
    graph.add((source, predicate, target))
    graph.add((target, inverse, source))


def build_instance_graph() -> Graph:
    graph = Graph()
    bind_prefixes(graph)
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/sample-data"), RDF.type, OWL.Ontology))
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/sample-data"), DCTERMS.title, Literal("Representative Airport Operations RDF Instances", lang="en")))
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/sample-data"), OWL.versionInfo, Literal(VERSION)))
    graph.add((URIRef(str(ONTOLOGY_IRI) + "/sample-data"), PROV.wasDerivedFrom, URIRef("urn:repo:digital-twin:sample-graph")))

    twins = json.loads((ROOT / "digital-twin" / "instances" / "sample-twins.json").read_text(encoding="utf-8"))
    relationships = json.loads((ROOT / "digital-twin" / "relationships" / "sample-relationships.json").read_text(encoding="utf-8"))
    airports = json.loads((ROOT / "data" / "reference" / "airports.json").read_text(encoding="utf-8"))["records"]
    airlines = json.loads((ROOT / "data" / "reference" / "airlines.json").read_text(encoding="utf-8"))["records"]
    config = json.loads((ROOT / "config" / "demo_config.json").read_text(encoding="utf-8"))

    model_to_class = {
        "Airport": "Airport", "Terminal": "Terminal", "Zone": "Zone", "Checkpoint": "Checkpoint",
        "Gate": "Gate", "Stand": "Stand", "AircraftType": "AircraftType", "Flight": "FlightOperation",
        "Queue": "PassengerFlowObservation", "BaggageAsset": "Asset", "Asset": "Asset",
        "MaintenanceAsset": "MaintenanceAsset", "EnergyMeter": "EnergyMeter",
        "MaintenanceWorkOrder": "MaintenanceWorkOrder", "Incident": "OperationalIncident",
    }
    property_map = {
        "airportId": "airportId", "terminalId": "terminalId", "zoneId": "zoneId",
        "checkpointId": "checkpointId", "gateId": "gateId", "standId": "standId",
        "assetId": "assetId", "aircraftTypeId": "aircraftTypeId", "flightEventId": "flightEventId",
        "workOrderId": "workOrderId", "incidentId": "incidentId", "queueId": "queueObservationId",
        "iataCode": "iataCode", "terminalCode": "terminalCode", "zoneType": "zoneType",
        "checkpointCode": "checkpointCode", "gateCode": "gateCode", "assetType": "assetType",
        "criticality": "criticality", "status": "status", "isSynthetic": "isSynthetic",
        "waitMinutes": "waitTimeMinutes", "passengerCount": "passengerCount",
    }
    decimal_properties = {"waitTimeMinutes"}
    integer_properties = {"passengerCount"}
    labels = ("airportName", "terminalCode", "zoneId", "checkpointName", "gateCode", "standName", "model", "syntheticFlightNumber", "queueId", "assetId", "workOrderId", "incidentId")
    operational_classes = {"FlightOperation", "PassengerFlowObservation", "MaintenanceWorkOrder", "OperationalIncident"}

    twin_resources: dict[str, URIRef] = {}
    for twin in twins:
        twin_id = twin["$dtId"]
        model_name = twin["$metadata"]["$model"].split(":")[-1].split(";")[0]
        class_name = model_to_class[model_name]
        node = resource(twin_id)
        twin_resources[twin_id] = node
        graph.add((node, RDF.type, AO[class_name]))
        graph.add((node, AO.twinIdentifier, Literal(twin_id)))
        graph.add((node, DCTERMS.identifier, Literal(twin_id)))
        label_value = next((str(twin[key]) for key in labels if key in twin), twin_id)
        graph.add((node, RDFS.label, Literal(label_value, lang="en")))
        classification = (
            "PublicReference" if twin.get("isSynthetic") is False
            else "SyntheticOperational" if class_name in operational_classes
            else "SyntheticMaster"
        )
        graph.add((node, AO.dataClassification, Literal(classification)))
        for source_name, target_name in property_map.items():
            if source_name not in twin:
                continue
            value = twin[source_name]
            if target_name in decimal_properties:
                literal = Literal(Decimal(str(value)))
            elif target_name in integer_properties:
                literal = Literal(int(value))
            else:
                literal = Literal(value)
            graph.add((node, AO[target_name], literal))

    airport_by_id = {item["airport_id"]: item for item in airports}
    primary_airport = twin_resources["SYN-TWIN-AP-CDG"]
    primary_reference = airport_by_id["SYN-AP-CDG"]
    graph.add((primary_airport, RDF.type, AO.PublicReferenceAnchor))
    graph.add((primary_airport, AO.latitude, Literal(Decimal(str(primary_reference["latitude"])))))
    graph.add((primary_airport, AO.longitude, Literal(Decimal(str(primary_reference["longitude"])))))
    graph.add((primary_airport, AO.icaoCode, Literal(primary_reference["icao_code"])))

    destination_reference = airport_by_id["SYN-AP-ORY"]
    destination = resource("SYN-TWIN-AP-ORY")
    graph.add((destination, RDF.type, AO.Airport))
    graph.add((destination, RDF.type, AO.PublicReferenceAnchor))
    graph.add((destination, AO.airportId, Literal(destination_reference["airport_id"])))
    graph.add((destination, AO.iataCode, Literal(destination_reference["iata_code"])))
    graph.add((destination, AO.icaoCode, Literal(destination_reference["icao_code"])))
    graph.add((destination, AO.isSynthetic, Literal(False)))
    graph.add((destination, AO.latitude, Literal(Decimal(str(destination_reference["latitude"])))))
    graph.add((destination, AO.longitude, Literal(Decimal(str(destination_reference["longitude"])))))
    graph.add((destination, RDFS.label, Literal(destination_reference["airport_name"], lang="en")))
    graph.add((destination, AO.dataClassification, Literal("PublicReference")))

    airline_reference = airlines[0]
    airline = resource(airline_reference["airline_id"])
    graph.add((airline, RDF.type, AO.Airline))
    graph.add((airline, RDF.type, AO.PublicReferenceAnchor))
    graph.add((airline, AO.airlineId, Literal(airline_reference["airline_id"])))
    graph.add((airline, AO.iataCode, Literal(airline_reference["iata_code"])))
    graph.add((airline, AO.icaoCode, Literal(airline_reference["icao_code"])))
    graph.add((airline, AO.isSynthetic, Literal(False)))
    graph.add((airline, RDFS.label, Literal(airline_reference["airline_name"], lang="en")))
    graph.add((airline, AO.dataClassification, Literal("PublicReference")))

    route = resource("SYN-ROUTE-CDG-ORY-REF-AL-001")
    graph.add((route, RDF.type, AO.Route))
    graph.add((route, AO.routeId, Literal("SYN-ROUTE-CDG-ORY-REF-AL-001")))
    graph.add((route, AO.isSynthetic, Literal(True)))
    graph.add((route, RDFS.label, Literal("Synthetic CDG to ORY demonstration route", lang="en")))
    add_inverse_pair(graph, route, AO.originAirport, primary_airport, AO.originForRoute)
    add_inverse_pair(graph, route, AO.destinationAirport, destination, AO.destinationForRoute)
    add_inverse_pair(graph, route, AO.routeOperatedByAirline, airline, AO.airlineOperatesRoute)

    relationship_map = {
        "contains": (AO.hasTerminal, AO.terminalOfAirport),
        "containsZones": (AO.hasZone, AO.zoneOfTerminal),
        "containsGates": (AO.hasGate, AO.gateOfTerminal),
        "containsCheckpoints": (AO.hasCheckpoint, AO.checkpointOfZone),
        "containsAssets": (AO.containsAsset, AO.assetLocatedInZone),
        "serves": (AO.servesStand, AO.standServedByGate),
        "servesFlight": (AO.servesFlight, AO.servedAtGate),
        "usesAircraftType": (AO.usesAircraftType, AO.aircraftTypeUsedByFlight),
        "monitoredBy": (AO.monitoredBy, AO.monitorsAsset),
        "hasWorkOrder": (AO.hasWorkOrder, AO.workOrderForAsset),
        "affects": (AO.affectsAsset, AO.affectedByIncident),
    }
    for relationship in relationships:
        source = twin_resources[relationship["$sourceId"]]
        target = twin_resources[relationship["$targetId"]]
        relationship_name = relationship["$relationshipName"]
        if relationship_name == "locatedIn":
            source_model = next(
                item["$metadata"]["$model"].split(":")[-1].split(";")[0]
                for item in twins if item["$dtId"] == relationship["$sourceId"]
            )
            predicate, inverse = (
                (AO.passengerFlowObservedInZone, AO.hasPassengerFlowObservation)
                if source_model == "Queue"
                else (AO.assetLocatedInZone, AO.containsAsset)
            )
        else:
            predicate, inverse = relationship_map[relationship_name]
        add_inverse_pair(graph, source, predicate, target, inverse)

    flight = twin_resources["SYN-TWIN-FLT-CDG-00001"]
    add_inverse_pair(graph, flight, AO.flightOperatedByAirline, airline, AO.airlineOperatesFlight)
    add_inverse_pair(graph, flight, AO.flightOnRoute, route, AO.routeHasFlight)
    graph.add((flight, AO.scheduledArrival, Literal("2026-01-01T07:00:00Z", datatype=XSD.dateTime)))
    graph.add((flight, AO.actualArrival, Literal("2026-01-01T07:04:00Z", datatype=XSD.dateTime)))
    graph.add((flight, AO.scheduledDeparture, Literal("2026-01-01T08:00:00Z", datatype=XSD.dateTime)))
    graph.add((flight, AO.actualDeparture, Literal("2026-01-01T08:09:00Z", datatype=XSD.dateTime)))
    graph.add((flight, AO.departureDelayMinutes, Literal(Decimal("9.0"))))

    turnaround = resource("SYN-TURN-CDG-00001")
    graph.add((turnaround, RDF.type, AO.Turnaround))
    graph.add((turnaround, AO.identifier, Literal("SYN-TURN-CDG-00001")))
    graph.add((turnaround, AO.isSynthetic, Literal(True)))
    graph.add((turnaround, AO.dataClassification, Literal("SyntheticOperational")))
    graph.add((turnaround, AO.turnaroundMinutes, Literal(Decimal("65.0"))))
    graph.add((turnaround, RDFS.label, Literal("Synthetic turnaround for SYN-FLT-CDG-00001", lang="en")))
    add_inverse_pair(graph, flight, AO.hasTurnaround, turnaround, AO.turnaroundOfFlight)

    queue = twin_resources["SYN-TWIN-QUE-CDG-01"]
    graph.add((queue, AO.eventTime, Literal("2026-01-01T07:15:00Z", datatype=XSD.dateTime)))
    graph.add((queue, AO.isSynthetic, Literal(True)))

    queue_measure = resource("MEASURE-AVG-QUEUE-WAIT-MIN")
    graph.add((queue_measure, RDF.type, AO.MeasureDefinition))
    graph.add((queue_measure, DCTERMS.identifier, Literal("Avg Queue Wait (min)")))
    graph.add((queue_measure, RDFS.label, Literal("Average queue wait", lang="en")))
    graph.add((queue_measure, AO.unitCode, Literal("min")))
    graph.add((queue_measure, AO.grainText, Literal("checkpoint and 15-minute interval")))
    graph.add((queue_measure, AO.formulaText, Literal("AVG(fact_passenger_queue_metrics.wait_time_min)")))
    graph.add((queue_measure, AO.formulaReference, Literal("semantic-model/measures.dax")))

    queue_measure_observation = resource("MEASURE-OBS-SYN-QUE-CDG-01")
    graph.add((queue_measure_observation, RDF.type, AO.MeasureObservation))
    graph.add((queue_measure_observation, AO.recordIdentifier, Literal("MEASURE-OBS-SYN-QUE-CDG-01")))
    graph.add((queue_measure_observation, AO.numericValue, Literal(Decimal("18.4"))))
    graph.add((queue_measure_observation, AO.valueType, Literal("actual")))
    graph.add((queue_measure_observation, AO.observationTimestamp, Literal(config["observation_timestamp"], datatype=XSD.dateTime)))
    add_inverse_pair(graph, queue_measure_observation, AO.observesMeasure, queue_measure, AO.hasObservation)
    add_inverse_pair(graph, queue_measure_observation, AO.observedFor, queue, AO.hasMeasureObservation)

    airport_dimension_record = resource("DIM-AIRPORT-SYN-AP-CDG")
    graph.add((airport_dimension_record, RDF.type, AO.AirportDimensionRecord))
    graph.add((airport_dimension_record, AO.recordIdentifier, Literal("SYN-AP-CDG")))
    add_inverse_pair(graph, airport_dimension_record, AO.representsEntity, primary_airport, AO.hasDimensionRecord)

    queue_fact_record = resource("FACT-QUEUE-SYN-QUE-CDG-01")
    graph.add((queue_fact_record, RDF.type, AO.PassengerQueueFactRecord))
    graph.add((queue_fact_record, AO.recordIdentifier, Literal("SYN-QUE-CDG-01")))
    add_inverse_pair(graph, queue_fact_record, AO.representsEvent, queue, AO.hasFactRecord)
    add_inverse_pair(graph, queue_fact_record, AO.hasDimensionMember, airport_dimension_record, AO.dimensionMemberOfFact)

    return graph


def serialize_graph(graph: Graph, format_name: str) -> bytes:
    if format_name == "pretty-xml":
        return serialize_deterministic_rdf_xml(graph)
    serialized = graph.serialize(format=format_name, encoding="utf-8")
    if not serialized.endswith(b"\n"):
        serialized += b"\n"
    return serialized


def serialize_deterministic_rdf_xml(graph: Graph) -> bytes:
    namespaces = {
        "ao": str(AO), "dcterms": str(DCTERMS), "owl": str(OWL), "prov": str(PROV),
        "qudt": str(QUDT), "rdf": str(RDF), "rdfs": str(RDFS), "skos": str(SKOS),
        "xsd": str(XSD),
    }
    for prefix, namespace in namespaces.items():
        ElementTree.register_namespace(prefix, namespace)
    root = ElementTree.Element(f"{{{RDF}}}RDF")
    for subject in sorted(set(graph.subjects()), key=lambda value: value.n3()):
        description = ElementTree.SubElement(root, f"{{{RDF}}}Description")
        if isinstance(subject, BNode):
            description.set(f"{{{RDF}}}nodeID", str(subject))
        else:
            description.set(f"{{{RDF}}}about", str(subject))
        statements = sorted(graph.predicate_objects(subject), key=lambda pair: (pair[0].n3(), pair[1].n3()))
        for predicate, obj in statements:
            _, namespace, local_name = graph.namespace_manager.compute_qname(predicate, generate=False)
            element = ElementTree.SubElement(description, f"{{{namespace}}}{local_name}")
            if isinstance(obj, URIRef):
                element.set(f"{{{RDF}}}resource", str(obj))
            elif isinstance(obj, BNode):
                element.set(f"{{{RDF}}}nodeID", str(obj))
            else:
                if obj.language:
                    element.set("{http://www.w3.org/XML/1998/namespace}lang", obj.language)
                elif obj.datatype:
                    element.set(f"{{{RDF}}}datatype", str(obj.datatype))
                element.text = str(obj)
    ElementTree.indent(root, space="  ")
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def generated_artifacts() -> dict[Path, bytes]:
    return {
        ONTOLOGY_PATH: serialize_graph(build_ontology_graph(), "turtle"),
        RDF_XML_PATH: serialize_graph(build_ontology_graph(), "pretty-xml"),
        SHACL_PATH: serialize_graph(build_shapes_graph(), "turtle"),
        INSTANCE_PATH: serialize_graph(build_instance_graph(), "turtle"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic airport-operations RDF artifacts.")
    parser.add_argument("--check", action="store_true", help="Fail if committed generated artifacts differ.")
    args = parser.parse_args()

    artifacts = generated_artifacts()
    differences = []
    for path, content in artifacts.items():
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                differences.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            print(f"generated {path.relative_to(ROOT).as_posix()}")
    if differences:
        raise SystemExit("generated ontology artifacts differ: " + ", ".join(differences))
    if args.check:
        print(f"ontology artifacts are deterministic and current ({len(artifacts)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())