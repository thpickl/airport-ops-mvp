from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import Graph, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF

from generate_ontology import AO, ONTOLOGY_IRI, ROOT


ONTOLOGY_DIR = ROOT / "ontology"
ONTOLOGY_PATH = ONTOLOGY_DIR / "airport-operations.ttl"
RDF_XML_PATH = ONTOLOGY_DIR / "airport-operations.rdf"
SHACL_PATH = ONTOLOGY_DIR / "airport-operations.shacl.ttl"
INSTANCE_PATH = ONTOLOGY_DIR / "instances" / "airport-operations-sample.ttl"
QUERY_DIR = ONTOLOGY_DIR / "queries"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_graph(path: Path, format_name: str) -> Graph:
    graph = Graph()
    graph.parse(path, format=format_name)
    require(len(graph) > 0, f"{path.relative_to(ROOT)} parsed as an empty graph")
    return graph


def validate_syntax_and_equivalence() -> tuple[Graph, Graph, Graph]:
    ontology = parse_graph(ONTOLOGY_PATH, "turtle")
    rdf_xml = parse_graph(RDF_XML_PATH, "xml")
    shapes = parse_graph(SHACL_PATH, "turtle")
    instances = parse_graph(INSTANCE_PATH, "turtle")
    require(isomorphic(ontology, rdf_xml), "Turtle and RDF/XML ontology graphs are not isomorphic")
    require((ONTOLOGY_IRI, RDF.type, OWL.Ontology) in ontology, "canonical ontology declaration is missing")
    require(any(ontology.objects(ONTOLOGY_IRI, OWL.versionIRI)), "owl:versionIRI is missing")
    return ontology, shapes, instances


def validate_owl_consistency(ontology: Graph, instances: Graph) -> int:
    object_properties = set(ontology.subjects(RDF.type, OWL.ObjectProperty))
    datatype_properties = set(ontology.subjects(RDF.type, OWL.DatatypeProperty))
    annotation_properties = set(ontology.subjects(RDF.type, OWL.AnnotationProperty))
    require(not object_properties & datatype_properties, "object/datatype property punning is not OWL 2 DL compatible")
    require(not object_properties & annotation_properties, "object/annotation property punning is not OWL 2 DL compatible")
    require(not datatype_properties & annotation_properties, "datatype/annotation property punning is not OWL 2 DL compatible")

    inferred = ontology + instances
    DeductiveClosure(OWLRL_Semantics).expand(inferred)
    require(not list(inferred.subjects(RDF.type, OWL.Nothing)), "OWL-RL inference produced an owl:Nothing individual")

    conflicts = []
    disjoint_pairs = set()
    for left, right in inferred.subject_objects(OWL.disjointWith):
        if isinstance(left, URIRef) and isinstance(right, URIRef):
            disjoint_pairs.add((left, right))
            disjoint_pairs.add((right, left))
    for subject in set(inferred.subjects(RDF.type, None)):
        types = {value for value in inferred.objects(subject, RDF.type) if isinstance(value, URIRef)}
        for left in types:
            for right in types:
                if (left, right) in disjoint_pairs:
                    conflicts.append((subject, left, right))
    require(not conflicts, f"individuals instantiate disjoint classes: {conflicts[:3]}")

    functional_properties = set(inferred.subjects(RDF.type, OWL.FunctionalProperty))
    functional_conflicts = []
    for predicate in functional_properties:
        for subject in set(inferred.subjects(predicate, None)):
            values = set(inferred.objects(subject, predicate))
            if len(values) > 1:
                functional_conflicts.append((subject, predicate, values))
    require(not functional_conflicts, f"functional-property conflicts: {functional_conflicts[:3]}")
    return len(inferred)


def validate_source_coverage(ontology: Graph) -> tuple[int, int]:
    base_contract = json.loads((ONTOLOGY_DIR / "airport-operations-ontology.yaml").read_text(encoding="utf-8"))
    enterprise_contract = json.loads((ONTOLOGY_DIR / "enterprise-ontology-extension.yaml").read_text(encoding="utf-8"))
    source_concepts = {item["name"] for item in base_contract["entities"] + enterprise_contract["entities"]}
    ontology_classes = {
        str(subject).removeprefix(str(AO))
        for subject in ontology.subjects(RDF.type, OWL.Class)
        if str(subject).startswith(str(AO))
    }
    missing_concepts = source_concepts - ontology_classes
    require(not missing_concepts, f"existing ontology concepts are missing: {sorted(missing_concepts)}")

    warehouse_sql = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "warehouse").glob("*.sql")))
    repository_model_text = warehouse_sql + "\n" + "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((ROOT / "notebooks").glob("*.ipynb"))
    )
    source_tables = {str(value) for value in ontology.objects(None, AO.sourceTable)}
    source_views = {str(value) for value in ontology.objects(None, AO.sourceView)}
    missing_tables = sorted(table for table in source_tables if table not in repository_model_text)
    missing_views = sorted(view for view in source_views if view not in warehouse_sql)
    require(not missing_tables, f"ontology source tables are absent from executable sources: {missing_tables}")
    require(not missing_views, f"ontology source views are absent from Warehouse SQL: {missing_views}")
    return len(source_tables), len(source_views)


def validate_shacl(ontology: Graph, shapes: Graph, instances: Graph) -> str:
    conforms, _, report_text = validate(
        data_graph=instances,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="owlrl",
        advanced=True,
        meta_shacl=True,
        allow_warnings=False,
    )
    require(bool(conforms), "SHACL validation failed:\n" + report_text)
    return report_text.splitlines()[0] if report_text else "Conforms"


def validate_queries(ontology: Graph, instances: Graph) -> dict[str, int]:
    query_graph = ontology + instances
    results = {}
    query_paths = sorted(QUERY_DIR.glob("*.rq"))
    require(len(query_paths) >= 5, "at least five competency queries are required")
    for path in query_paths:
        rows = list(query_graph.query(path.read_text(encoding="utf-8")))
        require(rows, f"competency query returned no rows: {path.name}")
        results[path.name] = len(rows)
    return results


def validate_determinism() -> None:
    completed = subprocess.run(
        [sys.executable, str(ONTOLOGY_DIR / "generate_ontology.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    require(completed.returncode == 0, (completed.stdout + completed.stderr).strip())


def main() -> int:
    ontology, shapes, instances = validate_syntax_and_equivalence()
    inferred_triples = validate_owl_consistency(ontology, instances)
    source_tables, source_views = validate_source_coverage(ontology)
    shacl_result = validate_shacl(ontology, shapes, instances)
    query_results = validate_queries(ontology, instances)
    validate_determinism()
    print(f"ontology triples: {len(ontology)}")
    print(f"representative instance triples: {len(instances)}")
    print(f"OWL-RL closure triples: {inferred_triples}")
    print(f"mapped source tables/views: {source_tables}/{source_views}")
    print(f"SHACL: {shacl_result}")
    print("competency queries: " + ", ".join(f"{name}={count}" for name, count in query_results.items()))
    print("ontology validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())