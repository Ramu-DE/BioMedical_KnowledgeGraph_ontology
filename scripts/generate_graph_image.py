"""
Generate a high-quality PNG image of the BioMedical Knowledge Graph.
Saves to BioMedical_KnowledgeGraph/visualization/BioMedical_KG.png
"""

import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NODES_DIR = PROJECT_DIR / "nodes"
RELS_DIR = PROJECT_DIR / "relationships"
OUTPUT_PATH = PROJECT_DIR / "visualization" / "BioMedical_KG.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Color scheme matching the Knwler visualization
TYPE_COLORS = {
    "Drug": "#e94560",
    "Disease": "#ff6b6b",
    "Gene": "#4ecdc4",
    "Protein": "#45b7d1",
    "Biomarker": "#96ceb4",
    "ClinicalTrial": "#ffeaa7",
    "Researcher": "#b8b8b8",
    "Institution": "#a29bfe",
    "AdverseEvent": "#fd79a8",
    "ResearchPaper": "#81ecec",
    "Pathway": "#55a3f0",
    "Anatomy": "#00b894",
    "CellType": "#6c5ce7",
    "BiologicalProcess": "#fdcb6e",
    "MolecularFunction": "#e17055",
    "Entity": "#636e72",
    "Exposure": "#d63031",
    "Phenotype": "#e84393",
    "Cluster": "#2d3436",
    "ClusterSummary": "#b2bec3",
}

# Node size by type (more important types get bigger nodes)
TYPE_SIZES = {
    "Drug": 300,
    "Disease": 280,
    "Gene": 220,
    "Protein": 200,
    "Pathway": 180,
    "Anatomy": 160,
    "ClinicalTrial": 150,
    "Biomarker": 140,
    "CellType": 140,
    "BiologicalProcess": 130,
    "MolecularFunction": 130,
    "Exposure": 160,
    "Phenotype": 160,
    "Entity": 140,
    "Researcher": 100,
    "Institution": 120,
    "AdverseEvent": 120,
    "ResearchPaper": 100,
    "Cluster": 200,
    "ClusterSummary": 100,
}


def load_csv(filepath):
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_graph():
    """Build a NetworkX graph from the CSV files."""
    G = nx.Graph()

    # Node configs: (filename, id_field, type_label)
    node_configs = [
        ("drugs.csv", "drug_id", "Drug"),
        ("diseases.csv", "disease_id", "Disease"),
        ("genes.csv", "gene_id", "Gene"),
        ("proteins.csv", "protein_id", "Protein"),
        ("biomarkers.csv", "biomarker_id", "Biomarker"),
        ("clinical_trials.csv", "trial_id", "ClinicalTrial"),
        ("researchers.csv", "researcher_id", "Researcher"),
        ("institutions.csv", "institution_id", "Institution"),
        ("adverse_events.csv", "event_id", "AdverseEvent"),
        ("research_papers.csv", "paper_id", "ResearchPaper"),
        ("pathways.csv", "pathway_id", "Pathway"),
        ("anatomy.csv", "anatomy_id", "Anatomy"),
        ("cell_types.csv", "cell_type_id", "CellType"),
        ("biological_processes.csv", "process_id", "BiologicalProcess"),
        ("molecular_functions.csv", "function_id", "MolecularFunction"),
        ("entities.csv", "entity_id", "Entity"),
        ("exposures.csv", "exposure_id", "Exposure"),
        ("phenotypes.csv", "phenotype_id", "Phenotype"),
        ("clusters.csv", "cluster_id", "Cluster"),
        ("cluster_summaries.csv", "summary_id", "ClusterSummary"),
    ]

    id_to_name = {}

    for filename, id_field, type_label in node_configs:
        rows = load_csv(NODES_DIR / filename)
        for row in rows:
            node_id = row.get(id_field, "")
            name = row.get("name", row.get("title", row.get("symbol", node_id)))
            id_to_name[node_id] = name
            G.add_node(node_id, name=name, node_type=type_label)

    # Relationship configs: (filename, src_field, tgt_field, rel_type)
    rel_configs = [
        ("drug_treats_disease.csv", "drug_id", "disease_id", "TREATS"),
        ("drug_targets_protein.csv", "drug_id", "protein_id", "TARGETS"),
        ("gene_associated_with_disease.csv", "gene_id", "disease_id", "ASSOCIATED_WITH"),
        ("biomarker_predicts_response.csv", "biomarker_id", "drug_id", "PREDICTS_RESPONSE"),
        ("trial_investigates_drug.csv", "trial_id", "drug_id", "INVESTIGATES"),
        ("trial_studies_disease.csv", "trial_id", "disease_id", "STUDIES"),
        ("trial_reports_adverse_event.csv", "trial_id", "event_id", "REPORTS"),
        ("institution_sponsors_trial.csv", "institution_id", "trial_id", "SPONSORS"),
        ("paper_authored_by.csv", "paper_id", "researcher_id", "AUTHORED_BY"),
        ("paper_mentions_disease.csv", "paper_id", "disease_id", "MENTIONS"),
        ("paper_mentions_drug.csv", "paper_id", "drug_id", "MENTIONS"),
        ("researcher_affiliated_with.csv", "researcher_id", "institution_id", "AFFILIATED_WITH"),
        ("gene_participates_in_pathway.csv", "gene_id", "pathway_id", "PARTICIPATES_IN"),
        ("protein_involved_in_pathway.csv", "protein_id", "pathway_id", "INVOLVED_IN"),
        ("pathway_involves_biological_process.csv", "pathway_id", "process_id", "REGULATES"),
        ("gene_involved_in_biological_process.csv", "gene_id", "process_id", "INVOLVED_IN"),
        ("protein_involved_in_biological_process.csv", "protein_id", "process_id", "INVOLVED_IN"),
        ("gene_has_molecular_function.csv", "gene_id", "function_id", "HAS_FUNCTION"),
        ("protein_has_molecular_function.csv", "protein_id", "function_id", "HAS_FUNCTION"),
        ("protein_expressed_in_anatomy.csv", "protein_id", "anatomy_id", "EXPRESSED_IN"),
        ("disease_affects_anatomy.csv", "disease_id", "anatomy_id", "AFFECTS"),
        ("cell_type_found_in_anatomy.csv", "cell_type_id", "anatomy_id", "FOUND_IN"),
        ("disease_involves_cell_type.csv", "disease_id", "cell_type_id", "INVOLVES"),
        ("cluster_has_summary.csv", "cluster_id", "summary_id", "HAS_SUMMARY"),
        ("disease_has_phenotype.csv", "disease_id", "phenotype_id", "HAS_PHENOTYPE"),
        ("exposure_increases_risk_disease.csv", "exposure_id", "disease_id", "INCREASES_RISK"),
        ("exposure_affects_gene.csv", "exposure_id", "gene_id", "AFFECTS"),
        ("entity_associated_with_disease.csv", "entity_id", "disease_id", "ASSOCIATED_WITH"),
        ("phenotype_associated_with_gene.csv", "phenotype_id", "gene_id", "ASSOCIATED_WITH"),
        ("node_belongs_to_cluster.csv", "node_id", "cluster_id", "BELONGS_TO"),
    ]

    for filename, src_field, tgt_field, rel_type in rel_configs:
        rows = load_csv(RELS_DIR / filename)
        for row in rows:
            src = row.get(src_field, "")
            tgt = row.get(tgt_field, "")
            if src in G.nodes and tgt in G.nodes:
                G.add_edge(src, tgt, rel_type=rel_type)

    return G, id_to_name


def render_graph(G, id_to_name):
    """Render the graph as a high-quality PNG."""

    # Figure setup - dark background like the Knwler visualization
    fig, ax = plt.subplots(1, 1, figsize=(24, 18), facecolor="#1a1a2e")
    ax.set_facecolor("#0f0f23")

    # Layout - spring layout with tuned parameters for readability
    print("  Computing layout...")
    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42)

    # Prepare node colors and sizes
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        ntype = G.nodes[node].get("node_type", "Entity")
        node_colors.append(TYPE_COLORS.get(ntype, "#666666"))
        node_sizes.append(TYPE_SIZES.get(ntype, 100))

    # Draw edges first (behind nodes)
    print("  Drawing edges...")
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#444466",
        alpha=0.3,
        width=0.5,
    )

    # Draw nodes
    print("  Drawing nodes...")
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9,
        edgecolors="#ffffff",
        linewidths=0.5,
    )

    # Draw labels for high-degree nodes only (to avoid clutter)
    print("  Adding labels...")
    degree_threshold = 3
    labels = {}
    for node in G.nodes():
        if G.degree(node) >= degree_threshold:
            name = G.nodes[node].get("name", node)
            # Truncate long names
            labels[node] = name[:20] + "..." if len(name) > 20 else name

    nx.draw_networkx_labels(
        G, pos, labels, ax=ax,
        font_size=6,
        font_color="#ffffff",
        font_weight="bold",
        alpha=0.9,
    )

    # Legend
    legend_patches = []
    type_counts = {}
    for node in G.nodes():
        ntype = G.nodes[node].get("node_type", "Unknown")
        type_counts[ntype] = type_counts.get(ntype, 0) + 1

    for ntype in sorted(type_counts.keys()):
        color = TYPE_COLORS.get(ntype, "#666666")
        count = type_counts[ntype]
        patch = mpatches.Patch(color=color, label=f"{ntype} ({count})")
        legend_patches.append(patch)

    legend = ax.legend(
        handles=legend_patches,
        loc="upper left",
        fontsize=8,
        framealpha=0.8,
        facecolor="#16213e",
        edgecolor="#0f3460",
        labelcolor="#ffffff",
        ncol=2,
    )

    # Title
    ax.set_title(
        f"BioMedical Knowledge Graph\n{G.number_of_nodes()} Nodes · {G.number_of_edges()} Relationships · 20 Types",
        fontsize=16,
        fontweight="bold",
        color="#e94560",
        pad=20,
    )

    ax.axis("off")
    plt.tight_layout(pad=1)

    # Save
    print(f"  Saving to: {OUTPUT_PATH}")
    plt.savefig(
        OUTPUT_PATH,
        dpi=200,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        pad_inches=0.5,
    )
    plt.close()
    print(f"  Done! Image size: {OUTPUT_PATH.stat().st_size / 1024:.0f} KB")


def main():
    print("=" * 60)
    print("GENERATING BIOMEDICAL KNOWLEDGE GRAPH IMAGE")
    print("=" * 60)

    print("\nBuilding graph from CSVs...")
    G, id_to_name = build_graph()
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    print("\nRendering graph image...")
    render_graph(G, id_to_name)

    print(f"\n{'='*60}")
    print(f"IMAGE SAVED: {OUTPUT_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
