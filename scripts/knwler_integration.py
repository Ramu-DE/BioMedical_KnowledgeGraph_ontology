"""
Knwler → BioMedical Knowledge Graph Integration Script
=======================================================
Processes Knwler's graph.json output and maps extracted entities/relationships
into the existing BioMedical KG CSV schema (20 node types, 30 relationship types).

Usage:
    python knwler_integration.py --input ./knwler_output/graph.json --output ./nodes/ --rel-output ./relationships/
    python knwler_integration.py --input ./knwler_output/ --batch  # process all graph.json files in directory

Prerequisites:
    pip install knwler
    # or
    pipx install knwler

Workflow:
    1. Run knwler on biomedical PDFs:
       knwler -f paper.pdf --backend openai --output ./knwler_output
    2. Run this script to map output into your KG CSVs:
       python knwler_integration.py --input ./knwler_output/graph.json
    3. Load updated CSVs into Neo4j/Neptune using existing Cypher scripts
"""

import json
import csv
import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Any


# =============================================================================
# ONTOLOGY MAPPING: Knwler entity types → BioMedical KG node types
# =============================================================================

ENTITY_TYPE_MAP = {
    # Drug mappings
    "drug": "Drug",
    "medication": "Drug",
    "pharmaceutical": "Drug",
    "compound": "Drug",
    "therapeutic": "Drug",
    "inhibitor": "Drug",
    "antibody": "Drug",
    # Disease mappings
    "disease": "Disease",
    "condition": "Disease",
    "disorder": "Disease",
    "syndrome": "Disease",
    "cancer": "Disease",
    "tumor": "Disease",
    "carcinoma": "Disease",
    # Gene mappings
    "gene": "Gene",
    "oncogene": "Gene",
    "tumor_suppressor": "Gene",
    # Protein mappings
    "protein": "Protein",
    "enzyme": "Protein",
    "receptor": "Protein",
    "kinase": "Protein",
    "antibody_target": "Protein",
    # Biomarker mappings
    "biomarker": "Biomarker",
    "marker": "Biomarker",
    "indicator": "Biomarker",
    # Clinical Trial mappings
    "clinical_trial": "ClinicalTrial",
    "trial": "ClinicalTrial",
    "study": "ClinicalTrial",
    # Researcher mappings
    "researcher": "Researcher",
    "scientist": "Researcher",
    "author": "Researcher",
    "investigator": "Researcher",
    # Institution mappings
    "institution": "Institution",
    "organization": "Institution",
    "university": "Institution",
    "hospital": "Institution",
    "company": "Institution",
    # Adverse Event mappings
    "adverse_event": "AdverseEvent",
    "side_effect": "AdverseEvent",
    "toxicity": "AdverseEvent",
    # Research Paper mappings
    "paper": "ResearchPaper",
    "publication": "ResearchPaper",
    "article": "ResearchPaper",
    # Pathway mappings
    "pathway": "Pathway",
    "signaling_pathway": "Pathway",
    "metabolic_pathway": "Pathway",
    # Anatomy mappings
    "anatomy": "Anatomy",
    "organ": "Anatomy",
    "tissue": "Anatomy",
    "body_part": "Anatomy",
    # Cell Type mappings
    "cell_type": "CellType",
    "cell": "CellType",
    # Biological Process mappings
    "biological_process": "BiologicalProcess",
    "process": "BiologicalProcess",
    # Molecular Function mappings
    "molecular_function": "MolecularFunction",
    "function": "MolecularFunction",
    # Entity mappings
    "entity": "Entity",
    "organism": "Entity",
    "pathogen": "Entity",
    "virus": "Entity",
    "bacterium": "Entity",
    "species": "Entity",
    # Exposure mappings
    "exposure": "Exposure",
    "risk_factor": "Exposure",
    "environmental_factor": "Exposure",
    "carcinogen": "Exposure",
    # Phenotype mappings
    "phenotype": "Phenotype",
    "symptom": "Phenotype",
    "clinical_feature": "Phenotype",
    "manifestation": "Phenotype",
}

# =============================================================================
# RELATIONSHIP MAPPING: Knwler relation types → BioMedical KG relationship types
# =============================================================================

RELATION_TYPE_MAP = {
    # Drug relationships
    "treats": ("Drug", "Disease", "drug_treats_disease"),
    "targets": ("Drug", "Protein", "drug_targets_protein"),
    "inhibits": ("Drug", "Protein", "drug_targets_protein"),
    "binds": ("Drug", "Protein", "drug_targets_protein"),
    # Gene relationships
    "associated_with": ("Gene", "Disease", "gene_associated_with_disease"),
    "causes": ("Gene", "Disease", "gene_associated_with_disease"),
    "predisposes": ("Gene", "Disease", "gene_associated_with_disease"),
    "participates_in": ("Gene", "Pathway", "gene_participates_in_pathway"),
    "involved_in": ("Gene", "BiologicalProcess", "gene_involved_in_biological_process"),
    "has_function": ("Gene", "MolecularFunction", "gene_has_molecular_function"),
    # Protein relationships
    "expressed_in": ("Protein", "Anatomy", "protein_expressed_in_anatomy"),
    # Disease relationships
    "affects": ("Disease", "Anatomy", "disease_affects_anatomy"),
    "involves": ("Disease", "CellType", "disease_involves_cell_type"),
    "has_phenotype": ("Disease", "Phenotype", "disease_has_phenotype"),
    "manifests_as": ("Disease", "Phenotype", "disease_has_phenotype"),
    # Exposure relationships
    "increases_risk": ("Exposure", "Disease", "exposure_increases_risk_disease"),
    "causes_mutation": ("Exposure", "Gene", "exposure_affects_gene"),
    # Biomarker relationships
    "predicts_response": ("Biomarker", "Drug", "biomarker_predicts_response"),
    "indicates": ("Biomarker", "Disease", "biomarker_predicts_response"),
    # Trial relationships
    "investigates": ("ClinicalTrial", "Drug", "trial_investigates_drug"),
    "studies": ("ClinicalTrial", "Disease", "trial_studies_disease"),
    "reports": ("ClinicalTrial", "AdverseEvent", "trial_reports_adverse_event"),
    # Institution relationships
    "sponsors": ("Institution", "ClinicalTrial", "institution_sponsors_trial"),
    "funds": ("Institution", "ClinicalTrial", "institution_sponsors_trial"),
    # Paper relationships
    "authored_by": ("ResearchPaper", "Researcher", "paper_authored_by"),
    "mentions_disease": ("ResearchPaper", "Disease", "paper_mentions_disease"),
    "mentions_drug": ("ResearchPaper", "Drug", "paper_mentions_drug"),
    # Researcher relationships
    "affiliated_with": ("Researcher", "Institution", "researcher_affiliated_with"),
    # Entity relationships
    "model_for": ("Entity", "Disease", "entity_associated_with_disease"),
    "host_of": ("Entity", "Disease", "entity_associated_with_disease"),
    # Phenotype relationships
    "linked_to_gene": ("Phenotype", "Gene", "phenotype_associated_with_gene"),
    # Cluster relationships
    "belongs_to": ("*", "Cluster", "node_belongs_to_cluster"),
    "has_summary": ("Cluster", "ClusterSummary", "cluster_has_summary"),
}

# =============================================================================
# CSV SCHEMAS: Column definitions for each node/relationship type
# =============================================================================

NODE_SCHEMAS = {
    "Drug": ["drug_id", "name", "generic_name", "drug_type", "approval_status", "approval_year", "mechanism"],
    "Disease": ["disease_id", "name", "category", "icd10_code", "prevalence"],
    "Gene": ["gene_id", "symbol", "name", "chromosome", "function"],
    "Protein": ["protein_id", "name", "uniprot_id", "protein_class", "cellular_location"],
    "Biomarker": ["biomarker_id", "name", "type", "measurement_unit", "clinical_significance"],
    "ClinicalTrial": ["trial_id", "nct_id", "title", "phase", "status", "start_date", "enrollment", "sponsor"],
    "Researcher": ["researcher_id", "name", "title", "specialization", "h_index", "total_publications"],
    "Institution": ["institution_id", "name", "type", "country", "city", "research_budget_millions"],
    "AdverseEvent": ["event_id", "name", "severity", "category", "frequency"],
    "ResearchPaper": ["paper_id", "title", "journal", "publication_date", "doi", "citations"],
    "Pathway": ["pathway_id", "name", "kegg_id", "category", "organism"],
    "Anatomy": ["anatomy_id", "name", "uberon_id", "system", "description"],
    "CellType": ["cell_type_id", "name", "cell_ontology_id", "category", "location"],
    "BiologicalProcess": ["process_id", "name", "go_id", "category", "description"],
    "MolecularFunction": ["function_id", "name", "go_id", "category", "description"],
    "Entity": ["entity_id", "name", "entity_type", "source", "description"],
    "Exposure": ["exposure_id", "name", "exposure_type", "category", "risk_level", "source"],
    "Phenotype": ["phenotype_id", "name", "hpo_id", "category", "description"],
    "Cluster": ["cluster_id", "name", "cluster_type", "algorithm", "node_count", "description"],
    "ClusterSummary": ["summary_id", "cluster_id", "summary_text", "key_entities", "therapeutic_relevance", "confidence_score"],
}

# ID prefixes for each node type
ID_PREFIXES = {
    "Drug": "D",
    "Disease": "DIS",
    "Gene": "G",
    "Protein": "P",
    "Biomarker": "BM",
    "ClinicalTrial": "CT",
    "Researcher": "R",
    "Institution": "INST",
    "AdverseEvent": "AE",
    "ResearchPaper": "RP",
    "Pathway": "PW",
    "Anatomy": "AN",
    "CellType": "CELL",
    "BiologicalProcess": "BP",
    "MolecularFunction": "MF",
    "Entity": "ENT",
    "Exposure": "EXP",
    "Phenotype": "PHE",
    "Cluster": "CLU",
    "ClusterSummary": "CS",
}


class KnwlerIntegrator:
    """Maps Knwler graph.json output to BioMedical KG CSV format."""

    def __init__(self, nodes_dir: str, relationships_dir: str):
        self.nodes_dir = Path(nodes_dir)
        self.relationships_dir = Path(relationships_dir)
        self.id_counters: dict[str, int] = {}
        self.entity_id_map: dict[str, str] = {}  # knwler_name → kg_id
        self.new_nodes: dict[str, list[dict]] = {k: [] for k in NODE_SCHEMAS}
        self.new_relationships: dict[str, list[dict]] = {}
        self._load_existing_ids()

    def _load_existing_ids(self):
        """Scan existing CSVs to determine next available IDs and build name→id index."""
        for node_type, schema in NODE_SCHEMAS.items():
            id_field = schema[0]
            prefix = ID_PREFIXES[node_type]
            max_id = 0

            csv_file = self._node_csv_path(node_type)
            if csv_file.exists():
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        id_val = row.get(id_field, "")
                        # Extract numeric part
                        num_part = re.sub(r"[^0-9]", "", id_val)
                        if num_part:
                            max_id = max(max_id, int(num_part))
                        # Index by name for deduplication
                        name = row.get("name", "").lower().strip()
                        if name:
                            self.entity_id_map[f"{node_type}:{name}"] = id_val

            self.id_counters[node_type] = max_id

    def _node_csv_path(self, node_type: str) -> Path:
        """Get the CSV file path for a node type."""
        type_to_file = {
            "Drug": "drugs.csv",
            "Disease": "diseases.csv",
            "Gene": "genes.csv",
            "Protein": "proteins.csv",
            "Biomarker": "biomarkers.csv",
            "ClinicalTrial": "clinical_trials.csv",
            "Researcher": "researchers.csv",
            "Institution": "institutions.csv",
            "AdverseEvent": "adverse_events.csv",
            "ResearchPaper": "research_papers.csv",
            "Pathway": "pathways.csv",
            "Anatomy": "anatomy.csv",
            "CellType": "cell_types.csv",
            "BiologicalProcess": "biological_processes.csv",
            "MolecularFunction": "molecular_functions.csv",
            "Entity": "entities.csv",
            "Exposure": "exposures.csv",
            "Phenotype": "phenotypes.csv",
            "Cluster": "clusters.csv",
            "ClusterSummary": "cluster_summaries.csv",
        }
        return self.nodes_dir / type_to_file[node_type]

    def _next_id(self, node_type: str) -> str:
        """Generate the next sequential ID for a node type."""
        self.id_counters[node_type] += 1
        prefix = ID_PREFIXES[node_type]
        return f"{prefix}{self.id_counters[node_type]:03d}"

    def _resolve_entity_type(self, knwler_type: str) -> str | None:
        """Map a Knwler entity type to a BioMedical KG node type."""
        normalized = knwler_type.lower().strip().replace(" ", "_")
        return ENTITY_TYPE_MAP.get(normalized)

    def _get_or_create_node(self, name: str, knwler_type: str, description: str = "") -> tuple[str | None, str | None]:
        """
        Look up or create a node. Returns (node_type, node_id) or (None, None) if unmapped.
        """
        kg_type = self._resolve_entity_type(knwler_type)
        if not kg_type:
            return None, None

        # Check if entity already exists
        key = f"{kg_type}:{name.lower().strip()}"
        if key in self.entity_id_map:
            return kg_type, self.entity_id_map[key]

        # Create new node
        node_id = self._next_id(kg_type)
        self.entity_id_map[key] = node_id

        # Build node record with available fields
        schema = NODE_SCHEMAS[kg_type]
        record = {field: "" for field in schema}
        record[schema[0]] = node_id  # ID field
        record["name"] = name

        if "description" in record:
            record["description"] = description
        if "entity_type" in record:
            record["entity_type"] = knwler_type
        if "source" in record and kg_type == "Entity":
            record["source"] = "Knwler extraction"
        if "source" in record and kg_type == "Exposure":
            record["source"] = "Knwler extraction"
        if "category" in record and not record["category"]:
            record["category"] = "Extracted"

        self.new_nodes[kg_type].append(record)
        return kg_type, node_id

    def process_graph_json(self, graph_json_path: str) -> dict[str, Any]:
        """
        Process a Knwler graph.json file and extract nodes/relationships.
        Returns statistics about what was processed.
        """
        with open(graph_json_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        stats = {
            "entities_processed": 0,
            "entities_mapped": 0,
            "entities_unmapped": 0,
            "relations_processed": 0,
            "relations_mapped": 0,
            "relations_unmapped": 0,
            "clusters_found": 0,
            "unmapped_types": set(),
        }

        # Process entities (nodes)
        entities = graph_data.get("entities", graph_data.get("nodes", []))
        for entity in entities:
            name = entity.get("name", "")
            etype = entity.get("type", "")
            description = entity.get("description", "")
            stats["entities_processed"] += 1

            kg_type, node_id = self._get_or_create_node(name, etype, description)
            if kg_type:
                stats["entities_mapped"] += 1
            else:
                stats["entities_unmapped"] += 1
                stats["unmapped_types"].add(etype)

        # Process relationships (edges)
        relations = graph_data.get("relations", graph_data.get("edges", graph_data.get("relationships", [])))
        for relation in relations:
            source_name = relation.get("source", "")
            target_name = relation.get("target", "")
            rel_type = relation.get("type", "").lower().strip().replace(" ", "_")
            description = relation.get("description", "")
            strength = relation.get("strength", "")
            stats["relations_processed"] += 1

            # Try to find source and target in our entity map
            source_id = self._find_entity_id(source_name)
            target_id = self._find_entity_id(target_name)

            if source_id and target_id:
                rel_record = {
                    "source_id": source_id,
                    "target_id": target_id,
                    "type": rel_type,
                    "description": description,
                    "strength": strength,
                    "source_name": source_name,
                    "target_name": target_name,
                }
                rel_file = self._resolve_relationship_file(rel_type, source_name, target_name)
                if rel_file not in self.new_relationships:
                    self.new_relationships[rel_file] = []
                self.new_relationships[rel_file].append(rel_record)
                stats["relations_mapped"] += 1
            else:
                stats["relations_unmapped"] += 1

        # Process clusters (communities)
        clusters = graph_data.get("clusters", graph_data.get("communities", []))
        for cluster in clusters:
            stats["clusters_found"] += 1
            cluster_name = cluster.get("topic", cluster.get("label", f"Cluster {stats['clusters_found']}"))
            cluster_id = self._next_id("Cluster")

            cluster_record = {
                "cluster_id": cluster_id,
                "name": cluster_name,
                "cluster_type": "Document-extracted",
                "algorithm": "Louvain",
                "node_count": str(len(cluster.get("entities", cluster.get("nodes", [])))),
                "description": cluster.get("description", f"Auto-detected cluster: {cluster_name}"),
            }
            self.new_nodes["Cluster"].append(cluster_record)
            self.entity_id_map[f"Cluster:{cluster_name.lower().strip()}"] = cluster_id

        # Convert unmapped_types set to list for JSON serialization
        stats["unmapped_types"] = list(stats["unmapped_types"])
        return stats

    def _find_entity_id(self, name: str) -> str | None:
        """Find an entity ID by name across all node types."""
        name_lower = name.lower().strip()
        for key, id_val in self.entity_id_map.items():
            if key.split(":", 1)[1] == name_lower:
                return id_val
        return None

    def _resolve_relationship_file(self, rel_type: str, source_name: str, target_name: str) -> str:
        """Determine which relationship CSV file to write to."""
        if rel_type in RELATION_TYPE_MAP:
            _, _, filename = RELATION_TYPE_MAP[rel_type]
            return filename
        # Fallback: generic extracted relationships file
        return "extracted_relationships"

    def write_outputs(self) -> dict[str, int]:
        """Write all new nodes and relationships to CSV files. Returns counts."""
        counts = {}

        # Write new nodes (append to existing CSVs)
        for node_type, records in self.new_nodes.items():
            if not records:
                continue
            csv_path = self._node_csv_path(node_type)
            file_exists = csv_path.exists()
            schema = NODE_SCHEMAS[node_type]

            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=schema, extrasaction="ignore")
                if not file_exists:
                    writer.writeheader()
                for record in records:
                    writer.writerow(record)

            counts[f"nodes_{node_type}"] = len(records)

        # Write extracted relationships
        for rel_file, records in self.new_relationships.items():
            if not records:
                continue
            csv_path = self.relationships_dir / f"{rel_file}.csv"
            file_exists = csv_path.exists()

            # Use a generic schema for extracted relationships
            fieldnames = ["source_id", "target_id", "type", "description", "strength", "source_name", "target_name"]

            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                if not file_exists:
                    writer.writeheader()
                for record in records:
                    writer.writerow(record)

            counts[f"rels_{rel_file}"] = len(records)

        return counts

    def generate_report(self, stats: dict, counts: dict) -> str:
        """Generate a human-readable integration report."""
        report = []
        report.append("=" * 60)
        report.append("KNWLER → BIOMEDICAL KG INTEGRATION REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 60)
        report.append("")
        report.append("EXTRACTION STATISTICS:")
        report.append(f"  Entities processed:  {stats['entities_processed']}")
        report.append(f"  Entities mapped:     {stats['entities_mapped']}")
        report.append(f"  Entities unmapped:   {stats['entities_unmapped']}")
        report.append(f"  Relations processed: {stats['relations_processed']}")
        report.append(f"  Relations mapped:    {stats['relations_mapped']}")
        report.append(f"  Relations unmapped:  {stats['relations_unmapped']}")
        report.append(f"  Clusters found:      {stats['clusters_found']}")
        report.append("")

        if stats["unmapped_types"]:
            report.append("UNMAPPED ENTITY TYPES (add to ENTITY_TYPE_MAP):")
            for t in sorted(stats["unmapped_types"]):
                report.append(f"  - {t}")
            report.append("")

        report.append("FILES WRITTEN:")
        for key, count in sorted(counts.items()):
            report.append(f"  {key}: {count} records")
        report.append("")
        report.append("=" * 60)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Integrate Knwler graph.json output into BioMedical Knowledge Graph CSVs"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to graph.json file or directory containing graph.json files"
    )
    parser.add_argument(
        "--nodes-dir",
        default="./nodes",
        help="Path to nodes CSV directory (default: ./nodes)"
    )
    parser.add_argument(
        "--rel-dir",
        default="./relationships",
        help="Path to relationships CSV directory (default: ./relationships)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all graph.json files in the input directory"
    )
    parser.add_argument(
        "--report",
        default="./integration_report.txt",
        help="Path to write the integration report"
    )

    args = parser.parse_args()

    # Resolve paths
    nodes_dir = Path(args.nodes_dir)
    rel_dir = Path(args.rel_dir)
    input_path = Path(args.input)

    if not nodes_dir.exists():
        nodes_dir.mkdir(parents=True)
    if not rel_dir.exists():
        rel_dir.mkdir(parents=True)

    integrator = KnwlerIntegrator(str(nodes_dir), str(rel_dir))

    # Collect graph.json files to process
    graph_files = []
    if args.batch and input_path.is_dir():
        graph_files = list(input_path.rglob("graph.json"))
    elif input_path.is_file():
        graph_files = [input_path]
    elif input_path.is_dir():
        graph_json = input_path / "graph.json"
        if graph_json.exists():
            graph_files = [graph_json]

    if not graph_files:
        print(f"ERROR: No graph.json files found at {input_path}")
        return

    print(f"Processing {len(graph_files)} graph file(s)...")

    all_stats = {
        "entities_processed": 0,
        "entities_mapped": 0,
        "entities_unmapped": 0,
        "relations_processed": 0,
        "relations_mapped": 0,
        "relations_unmapped": 0,
        "clusters_found": 0,
        "unmapped_types": set(),
    }

    for gf in graph_files:
        print(f"  Processing: {gf}")
        stats = integrator.process_graph_json(str(gf))
        for key in ["entities_processed", "entities_mapped", "entities_unmapped",
                    "relations_processed", "relations_mapped", "relations_unmapped",
                    "clusters_found"]:
            all_stats[key] += stats[key]
        all_stats["unmapped_types"].update(stats["unmapped_types"])

    # Write outputs
    counts = integrator.write_outputs()

    # Generate report
    all_stats["unmapped_types"] = list(all_stats["unmapped_types"])
    report = integrator.generate_report(all_stats, counts)
    print(report)

    # Save report
    report_path = Path(args.report)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
