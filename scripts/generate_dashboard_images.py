"""
Generate dashboard PNG images from the BioMedical Knowledge Graph.
Creates multiple high-quality images matching the analytics dashboard style.
"""

import csv
import math
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import networkx as nx

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NODES_DIR = PROJECT_DIR / "nodes"
RELS_DIR = PROJECT_DIR / "relationships"
VIZ_DIR = PROJECT_DIR / "visualization"
VIZ_DIR.mkdir(parents=True, exist_ok=True)

TYPE_COLORS = {
    "Drug": "#e94560", "Disease": "#ff6b6b", "Gene": "#4ecdc4",
    "Protein": "#45b7d1", "Biomarker": "#96ceb4", "ClinicalTrial": "#ffeaa7",
    "Researcher": "#b8b8b8", "Institution": "#a29bfe", "AdverseEvent": "#fd79a8",
    "ResearchPaper": "#81ecec", "Pathway": "#55a3f0", "Anatomy": "#00b894",
    "CellType": "#6c5ce7", "BiologicalProcess": "#fdcb6e", "MolecularFunction": "#e17055",
    "Entity": "#636e72", "Exposure": "#d63031", "Phenotype": "#e84393",
    "Cluster": "#2d3436", "ClusterSummary": "#b2bec3",
}


def load_csv(filepath):
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_graph():
    G = nx.Graph()
    id_to_meta = {}

    node_configs = [
        ("drugs.csv", "drug_id", "Drug"), ("diseases.csv", "disease_id", "Disease"),
        ("genes.csv", "gene_id", "Gene"), ("proteins.csv", "protein_id", "Protein"),
        ("biomarkers.csv", "biomarker_id", "Biomarker"), ("clinical_trials.csv", "trial_id", "ClinicalTrial"),
        ("researchers.csv", "researcher_id", "Researcher"), ("institutions.csv", "institution_id", "Institution"),
        ("adverse_events.csv", "event_id", "AdverseEvent"), ("research_papers.csv", "paper_id", "ResearchPaper"),
        ("pathways.csv", "pathway_id", "Pathway"), ("anatomy.csv", "anatomy_id", "Anatomy"),
        ("cell_types.csv", "cell_type_id", "CellType"), ("biological_processes.csv", "process_id", "BiologicalProcess"),
        ("molecular_functions.csv", "function_id", "MolecularFunction"), ("entities.csv", "entity_id", "Entity"),
        ("exposures.csv", "exposure_id", "Exposure"), ("phenotypes.csv", "phenotype_id", "Phenotype"),
        ("clusters.csv", "cluster_id", "Cluster"), ("cluster_summaries.csv", "summary_id", "ClusterSummary"),
    ]

    for filename, id_field, type_label in node_configs:
        rows = load_csv(NODES_DIR / filename)
        for row in rows:
            node_id = row.get(id_field, "")
            name = row.get("name", row.get("title", row.get("symbol", node_id)))
            desc = row.get("description", row.get("mechanism", row.get("function", "")))
            G.add_node(node_id, name=name, node_type=type_label, description=desc)
            id_to_meta[node_id] = {"name": name, "type": type_label, "description": desc}

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

    rel_type_counter = Counter()
    for filename, src_field, tgt_field, rel_type in rel_configs:
        rows = load_csv(RELS_DIR / filename)
        for row in rows:
            src = row.get(src_field, "")
            tgt = row.get(tgt_field, "")
            if src in G.nodes and tgt in G.nodes:
                G.add_edge(src, tgt, rel_type=rel_type)
                rel_type_counter[rel_type] += 1

    return G, id_to_meta, rel_type_counter


def generate_overview_image(G, rel_type_counter):
    """Generate the overview stats + distribution charts image."""
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    avg_degree = round(2 * num_edges / num_nodes, 2)
    max_edges = num_nodes * (num_nodes - 1) / 2
    density = num_edges / max_edges if max_edges > 0 else 0
    components = list(nx.connected_components(G))
    num_components = len(components)
    largest = max(len(c) for c in components)
    largest_pct = round(100 * largest / num_nodes, 1)
    clusters_csv = load_csv(NODES_DIR / "clusters.csv")
    num_clusters = len(clusters_csv)

    fig = plt.figure(figsize=(20, 14), facecolor="#0a0a1a")

    # Title
    fig.text(0.03, 0.96, "BioMedical Knowledge Graph", fontsize=20, fontweight="bold", color="#ffffff", va="top")
    fig.text(0.03, 0.925, f"Analytics Dashboard  •  {num_nodes} entities  •  {num_edges} relations  •  20 node types  •  30 relationship types",
             fontsize=10, color="#8888aa", va="top")

    # Stats cards row
    stats = [
        (str(num_nodes), "ENTITIES"),
        (str(num_edges), "RELATIONS"),
        (str(num_clusters), "CLUSTERS"),
        (str(avg_degree), "AVG DEGREE"),
        (f"{density*1000:.1f}/1000", "NETWORK\nDENSITY"),
        (str(num_components), "COMPONENTS"),
        (f"{largest_pct}%", "LARGEST\nCOMPONENT"),
    ]

    for i, (value, label) in enumerate(stats):
        ax = fig.add_axes([0.03 + i * 0.135, 0.78, 0.12, 0.1])
        ax.set_facecolor("#1a1a3e")
        for spine in ax.spines.values():
            spine.set_color("#1e1e3f")
            spine.set_linewidth(1.5)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.65, value, fontsize=18, fontweight="bold", color="#4fc3f7",
                ha="center", va="center", transform=ax.transAxes)
        ax.text(0.5, 0.2, label, fontsize=7, color="#8888aa",
                ha="center", va="center", transform=ax.transAxes)

    # Entity Type Distribution (left chart)
    ax1 = fig.add_axes([0.05, 0.08, 0.42, 0.62])
    ax1.set_facecolor("#12122a")
    for spine in ax1.spines.values():
        spine.set_color("#1e1e3f")

    type_counter = Counter()
    for node in G.nodes():
        ntype = G.nodes[node].get("node_type", "Unknown")
        type_counter[ntype] += 1
    type_data = sorted(type_counter.items(), key=lambda x: x[1], reverse=True)

    types = [t[0] for t in type_data]
    counts = [t[1] for t in type_data]
    colors = [TYPE_COLORS.get(t, "#666") for t in types]

    y_pos = range(len(types))
    ax1.barh(y_pos, counts, color=colors, height=0.7, edgecolor="none")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(types, fontsize=8, color="#e0e0e0")
    ax1.set_xlabel("Count", fontsize=9, color="#8888aa")
    ax1.tick_params(axis="x", colors="#8888aa", labelsize=8)
    ax1.set_title("ENTITY TYPES", fontsize=10, fontweight="bold", color="#e0e0e0", pad=10)
    ax1.invert_yaxis()
    ax1.grid(axis="x", color="#1e1e3f", linewidth=0.5)

    # Relation Type Distribution (right chart)
    ax2 = fig.add_axes([0.55, 0.08, 0.42, 0.62])
    ax2.set_facecolor("#12122a")
    for spine in ax2.spines.values():
        spine.set_color("#1e1e3f")

    rel_data = sorted(rel_type_counter.items(), key=lambda x: x[1], reverse=True)[:15]
    rel_types = [t[0] for t in rel_data]
    rel_counts = [t[1] for t in rel_data]
    rel_colors = ["#4fc3f7", "#e94560", "#4ecdc4", "#ffeaa7", "#a29bfe",
                  "#fd79a8", "#00b894", "#fdcb6e", "#6c5ce7", "#e17055",
                  "#81ecec", "#55a3f0", "#96ceb4", "#d63031", "#b2bec3"]

    y_pos2 = range(len(rel_types))
    ax2.barh(y_pos2, rel_counts, color=rel_colors[:len(rel_types)], height=0.7, edgecolor="none")
    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels(rel_types, fontsize=8, color="#e0e0e0")
    ax2.set_xlabel("Count", fontsize=9, color="#8888aa")
    ax2.tick_params(axis="x", colors="#8888aa", labelsize=8)
    ax2.set_title("RELATION TYPES", fontsize=10, fontweight="bold", color="#e0e0e0", pad=10)
    ax2.invert_yaxis()
    ax2.grid(axis="x", color="#1e1e3f", linewidth=0.5)

    output = VIZ_DIR / "dashboard_overview.png"
    plt.savefig(output, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.3)
    plt.close()
    print(f"  Saved: {output}")
    return output


def generate_pagerank_image(G, id_to_meta):
    """Generate the PageRank table as an image."""
    pagerank = nx.pagerank(G)
    top = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:15]

    fig, ax = plt.subplots(figsize=(16, 8), facecolor="#0a0a1a")
    ax.set_facecolor("#0a0a1a")
    ax.axis("off")

    # Title
    ax.text(0.02, 0.95, "Most Important Entities (PageRank)", fontsize=14, fontweight="bold",
            color="#e0e0e0", transform=ax.transAxes, va="top")
    ax.text(0.02, 0.89, "PageRank measures global importance — entities referenced by many highly-connected entities score highest.",
            fontsize=9, color="#8888aa", transform=ax.transAxes, va="top")

    # Table header
    headers = ["#", "ENTITY", "TYPE", "SCORE", "DEGREE", "DESCRIPTION"]
    col_x = [0.02, 0.06, 0.35, 0.52, 0.72, 0.80]
    y_start = 0.82
    row_height = 0.05

    for i, h in enumerate(headers):
        ax.text(col_x[i], y_start, h, fontsize=7, fontweight="bold", color="#8888aa",
                transform=ax.transAxes, va="center")

    # Separator line
    ax.plot([0.02, 0.98], [y_start - 0.015, y_start - 0.015], color="#1e1e3f", linewidth=1,
            transform=ax.transAxes, clip_on=False)

    # Table rows
    max_score = top[0][1] if top else 1
    for i, (node_id, score) in enumerate(top):
        y = y_start - (i + 1) * row_height
        meta = id_to_meta.get(node_id, {})
        name = meta.get("name", node_id)[:30]
        ntype = meta.get("type", "Unknown")
        desc = meta.get("description", "")[:40]
        degree = G.degree(node_id)
        color = TYPE_COLORS.get(ntype, "#666")

        # Row background (alternating)
        if i % 2 == 0:
            rect = mpatches.FancyBboxPatch((0.01, y - row_height * 0.4), 0.98, row_height * 0.8,
                                           boxstyle="square", facecolor="#12122a", alpha=0.5,
                                           transform=ax.transAxes, clip_on=False)
            ax.add_patch(rect)

        ax.text(col_x[0], y, str(i + 1), fontsize=9, color="#4fc3f7",
                transform=ax.transAxes, va="center", fontweight="bold")
        ax.text(col_x[1], y, name, fontsize=9, color="#ffffff",
                transform=ax.transAxes, va="center", fontweight="bold")
        ax.text(col_x[2], y, ntype, fontsize=8, color=color,
                transform=ax.transAxes, va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=color, alpha=0.2, edgecolor=color, linewidth=0.5))
        ax.text(col_x[3], y, f"{score:.5f}", fontsize=8, color="#8888aa",
                transform=ax.transAxes, va="center")
        ax.text(col_x[4], y, str(degree), fontsize=9, color="#e0e0e0",
                transform=ax.transAxes, va="center")
        ax.text(col_x[5], y, desc, fontsize=7, color="#666688",
                transform=ax.transAxes, va="center")

    output = VIZ_DIR / "dashboard_pagerank.png"
    plt.savefig(output, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.3)
    plt.close()
    print(f"  Saved: {output}")
    return output


def generate_network_image(G, id_to_meta):
    """Generate the network visualization image."""
    fig, ax = plt.subplots(figsize=(20, 16), facecolor="#080818")
    ax.set_facecolor("#080818")

    # Compute layout
    pos = nx.spring_layout(G, k=2.2, iterations=80, seed=42)

    # PageRank for node sizing
    pagerank = nx.pagerank(G)
    max_pr = max(pagerank.values())

    # Draw edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#222244", alpha=0.25, width=0.4)

    # Draw nodes by type
    for ntype, color in TYPE_COLORS.items():
        nodelist = [n for n in G.nodes() if G.nodes[n].get("node_type") == ntype]
        if not nodelist:
            continue
        sizes = [60 + (pagerank.get(n, 0) / max_pr) * 500 for n in nodelist]
        nx.draw_networkx_nodes(G, pos, nodelist=nodelist, ax=ax,
                               node_color=color, node_size=sizes,
                               alpha=0.85, edgecolors="#ffffff", linewidths=0.3)

    # Labels for top nodes only
    top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:25]
    labels = {n: id_to_meta.get(n, {}).get("name", n)[:18] for n, _ in top_nodes}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7, font_color="#ffffff", font_weight="bold")

    # Legend
    legend_patches = []
    type_counter = Counter(G.nodes[n].get("node_type", "Unknown") for n in G.nodes())
    for ntype in sorted(type_counter.keys()):
        color = TYPE_COLORS.get(ntype, "#666")
        legend_patches.append(mpatches.Patch(color=color, label=f"{ntype} ({type_counter[ntype]})"))

    legend = ax.legend(handles=legend_patches, loc="lower left", fontsize=7,
                       framealpha=0.85, facecolor="#12122a", edgecolor="#1e1e3f",
                       labelcolor="#e0e0e0", ncol=2)

    ax.set_title("BioMedical Knowledge Graph — Network Visualization",
                 fontsize=14, fontweight="bold", color="#4fc3f7", pad=15)
    ax.axis("off")

    output = VIZ_DIR / "dashboard_network.png"
    plt.savefig(output, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.2)
    plt.close()
    print(f"  Saved: {output}")
    return output


def main():
    print("=" * 60)
    print("GENERATING DASHBOARD IMAGES")
    print("=" * 60)

    print("\nBuilding graph...")
    G, id_to_meta, rel_type_counter = build_graph()
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    print("\nGenerating overview image (stats + charts)...")
    generate_overview_image(G, rel_type_counter)

    print("\nGenerating PageRank table image...")
    generate_pagerank_image(G, id_to_meta)

    print("\nGenerating network visualization image...")
    generate_network_image(G, id_to_meta)

    print(f"\n{'='*60}")
    print("ALL DASHBOARD IMAGES SAVED TO:")
    print(f"  {VIZ_DIR / 'dashboard_overview.png'}")
    print(f"  {VIZ_DIR / 'dashboard_pagerank.png'}")
    print(f"  {VIZ_DIR / 'dashboard_network.png'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
