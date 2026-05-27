"""
Generate a rich analytics dashboard for the BioMedical Knowledge Graph.
Produces an interactive HTML file with:
- Overview stats cards (entities, relations, clusters, avg degree, density)
- Entity type distribution chart
- Relation type distribution chart
- Most Important Entities (PageRank) table
- Interactive force-directed graph visualization with community coloring
- Dark theme matching the Knwler analytics style

Usage:
    python generate_dashboard.py
    python generate_dashboard.py --open
"""

import csv
import json
import math
import argparse
from pathlib import Path
from collections import Counter
from datetime import datetime

# Try importing networkx for graph analytics
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("WARNING: networkx not installed. Install with: pip install networkx")

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NODES_DIR = PROJECT_DIR / "nodes"
RELS_DIR = PROJECT_DIR / "relationships"
OUTPUT_PATH = PROJECT_DIR / "visualization" / "dashboard.html"


def load_csv(filepath):
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_graph():
    """Build NetworkX graph and collect metadata."""
    G = nx.Graph()
    entities = []
    id_to_meta = {}

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


def compute_analytics(G):
    """Compute graph analytics."""
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    # Average degree
    avg_degree = round(2 * num_edges / num_nodes, 2) if num_nodes > 0 else 0

    # Network density
    max_edges = num_nodes * (num_nodes - 1) / 2
    density = round(num_edges / max_edges, 6) if max_edges > 0 else 0
    density_display = f"{density * 1000:.1f}/1000"

    # Connected components
    components = list(nx.connected_components(G))
    num_components = len(components)
    largest_component = max(len(c) for c in components) if components else 0
    largest_pct = round(100 * largest_component / num_nodes, 1) if num_nodes > 0 else 0

    # Clusters (from community detection)
    clusters_csv = load_csv(NODES_DIR / "clusters.csv")
    num_clusters = len(clusters_csv)

    # PageRank
    pagerank = nx.pagerank(G)

    # Top entities by PageRank
    top_entities = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:20]

    # Node type distribution
    type_counter = Counter()
    for node in G.nodes():
        ntype = G.nodes[node].get("node_type", "Unknown")
        type_counter[ntype] += 1

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "num_clusters": num_clusters,
        "avg_degree": avg_degree,
        "density_display": density_display,
        "num_components": num_components,
        "largest_pct": largest_pct,
        "pagerank": pagerank,
        "top_entities": top_entities,
        "type_counter": type_counter,
    }


def generate_dashboard_html(G, id_to_meta, rel_type_counter, analytics):
    """Generate the full dashboard HTML."""

    # Prepare data for charts
    type_data = sorted(analytics["type_counter"].items(), key=lambda x: x[1], reverse=True)
    rel_data = sorted(rel_type_counter.items(), key=lambda x: x[1], reverse=True)[:15]

    # Prepare top entities table
    top_rows = ""
    for i, (node_id, score) in enumerate(analytics["top_entities"], 1):
        meta = id_to_meta.get(node_id, {})
        name = meta.get("name", node_id)
        ntype = meta.get("type", "Unknown")
        desc = meta.get("description", "")[:80]
        degree = G.degree(node_id)
        top_rows += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{name}</strong></td>
                <td><span class="type-badge">{ntype}</span></td>
                <td><div class="score-bar"><div class="score-fill" style="width:{score*100/analytics['top_entities'][0][1]:.0f}%"></div><span>{score:.5f}</span></div></td>
                <td>{degree}</td>
                <td class="desc-cell">{desc}</td>
            </tr>"""

    # Prepare graph data for vis.js
    type_colors = {
        "Drug": "#e94560", "Disease": "#ff6b6b", "Gene": "#4ecdc4",
        "Protein": "#45b7d1", "Biomarker": "#96ceb4", "ClinicalTrial": "#ffeaa7",
        "Researcher": "#b8b8b8", "Institution": "#a29bfe", "AdverseEvent": "#fd79a8",
        "ResearchPaper": "#81ecec", "Pathway": "#55a3f0", "Anatomy": "#00b894",
        "CellType": "#6c5ce7", "BiologicalProcess": "#fdcb6e", "MolecularFunction": "#e17055",
        "Entity": "#636e72", "Exposure": "#d63031", "Phenotype": "#e84393",
        "Cluster": "#2d3436", "ClusterSummary": "#b2bec3",
    }

    # Build nodes JSON for vis.js
    pagerank = analytics["pagerank"]
    max_pr = max(pagerank.values()) if pagerank else 1
    nodes_json = []
    for node in G.nodes():
        meta = id_to_meta.get(node, {})
        ntype = meta.get("type", "Unknown")
        pr = pagerank.get(node, 0)
        size = 8 + (pr / max_pr) * 40
        nodes_json.append({
            "id": node,
            "label": meta.get("name", node)[:25],
            "color": type_colors.get(ntype, "#666"),
            "size": round(size, 1),
            "title": f"{meta.get('name', node)}\nType: {ntype}\nDegree: {G.degree(node)}\nPageRank: {pr:.5f}",
        })

    edges_json = []
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        edges_json.append({
            "from": u,
            "to": v,
            "title": data.get("rel_type", ""),
        })

    # Entity type chart data
    entity_chart_labels = json.dumps([t[0] for t in type_data])
    entity_chart_values = json.dumps([t[1] for t in type_data])
    entity_chart_colors = json.dumps([type_colors.get(t[0], "#666") for t in type_data])

    # Relation type chart data
    rel_chart_labels = json.dumps([t[0] for t in rel_data])
    rel_chart_values = json.dumps([t[1] for t in rel_data])

    date_str = datetime.now().strftime("%Y-%m-%d")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BioMedical Knowledge Graph - Analytics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/vis-network.min.js"></script>
<style>
:root {{
    --bg: #0a0a1a;
    --card-bg: #12122a;
    --card-border: #1e1e3f;
    --text: #e0e0e0;
    --text-muted: #8888aa;
    --accent: #4fc3f7;
    --accent2: #e94560;
    --stat-bg: #1a1a3e;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
.header {{ padding:24px 40px; border-bottom:1px solid var(--card-border); display:flex; justify-content:space-between; align-items:center; }}
.header h1 {{ font-size:1.4rem; font-weight:700; }}
.header .subtitle {{ font-size:0.85rem; color:var(--text-muted); margin-top:4px; }}
.toggle-btn {{ padding:6px 14px; border:1px solid var(--accent); background:transparent; color:var(--accent); border-radius:4px; cursor:pointer; font-size:0.8rem; }}
.toggle-btn:hover {{ background:var(--accent); color:#000; }}
.container {{ max-width:1400px; margin:0 auto; padding:30px 40px; }}

/* Stats Cards */
.stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:16px; margin-bottom:40px; }}
.stat-card {{ background:var(--stat-bg); border:1px solid var(--card-border); border-radius:12px; padding:20px; text-align:center; }}
.stat-card .value {{ font-size:1.8rem; font-weight:700; color:var(--accent); }}
.stat-card .label {{ font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); margin-top:4px; }}

/* Section */
.section {{ margin-bottom:40px; }}
.section h2 {{ font-size:1.1rem; font-weight:600; margin-bottom:16px; padding-bottom:8px; border-bottom:1px solid var(--card-border); }}

/* Charts */
.charts-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:40px; }}
.chart-card {{ background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:24px; }}
.chart-card h3 {{ font-size:0.95rem; font-weight:600; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.5px; }}

/* Table */
.table-card {{ background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:24px; overflow-x:auto; }}
.table-card h3 {{ font-size:0.95rem; font-weight:600; margin-bottom:8px; }}
.table-card p {{ font-size:0.8rem; color:var(--text-muted); margin-bottom:16px; }}
table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
th {{ text-align:left; padding:10px 12px; border-bottom:2px solid var(--card-border); color:var(--text-muted); font-weight:600; text-transform:uppercase; font-size:0.7rem; letter-spacing:0.5px; }}
td {{ padding:10px 12px; border-bottom:1px solid var(--card-border); }}
tr:hover {{ background:rgba(79,195,247,0.05); }}
.type-badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.7rem; background:var(--accent2); color:#fff; }}
.score-bar {{ display:flex; align-items:center; gap:8px; }}
.score-fill {{ height:6px; background:var(--accent); border-radius:3px; min-width:4px; }}
.score-bar span {{ font-size:0.75rem; color:var(--text-muted); white-space:nowrap; }}
.desc-cell {{ max-width:250px; font-size:0.75rem; color:var(--text-muted); }}

/* Graph */
.graph-section {{ background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:24px; margin-bottom:40px; }}
.graph-section h3 {{ font-size:0.95rem; font-weight:600; margin-bottom:16px; text-transform:uppercase; }}
#graph-container {{ width:100%; height:600px; border-radius:8px; background:#080818; }}

/* Legend */
.legend {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
.legend-item {{ display:flex; align-items:center; gap:4px; font-size:0.7rem; color:var(--text-muted); }}
.legend-dot {{ width:10px; height:10px; border-radius:50%; }}

@media (max-width:900px) {{
    .charts-grid {{ grid-template-columns:1fr; }}
    .stats-grid {{ grid-template-columns:repeat(3, 1fr); }}
}}
</style>
</head>
<body>
<div class="header">
    <div>
        <h1>BioMedical Knowledge Graph</h1>
        <div class="subtitle">Knwler generated on {date_str} &middot; {analytics['num_nodes']} entities &middot; {analytics['num_edges']} relations from CSV ontology</div>
    </div>
    <button class="toggle-btn" onclick="document.body.style.background=document.body.style.background==='#f5f5f5'?'#0a0a1a':'#f5f5f5'">Toggle Theme</button>
</div>

<div class="container">
    <!-- Overview Stats -->
    <div class="section">
        <h2>Overview</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="value">{analytics['num_nodes']}</div><div class="label">Entities</div></div>
            <div class="stat-card"><div class="value">{analytics['num_edges']}</div><div class="label">Relations</div></div>
            <div class="stat-card"><div class="value">{analytics['num_clusters']}</div><div class="label">Clusters</div></div>
            <div class="stat-card"><div class="value">{analytics['avg_degree']}</div><div class="label">Avg Degree</div></div>
            <div class="stat-card"><div class="value">{analytics['density_display']}</div><div class="label">Network Density</div></div>
            <div class="stat-card"><div class="value">{analytics['num_components']}</div><div class="label">Components</div></div>
            <div class="stat-card"><div class="value">{analytics['largest_pct']}%</div><div class="label">Largest Component</div></div>
        </div>
    </div>

    <!-- Distribution Charts -->
    <div class="section">
        <h2>Distribution</h2>
        <div class="charts-grid">
            <div class="chart-card">
                <h3>Entity Types</h3>
                <canvas id="entityChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Relation Types</h3>
                <canvas id="relChart"></canvas>
            </div>
        </div>
    </div>

    <!-- PageRank Table -->
    <div class="section">
        <div class="table-card">
            <h3>Most Important Entities (PageRank)</h3>
            <p>PageRank measures global importance — entities that are referenced by many other highly-connected entities score highest.</p>
            <table>
                <thead><tr><th>#</th><th>Entity</th><th>Type</th><th>Score</th><th>Degree</th><th>Description</th></tr></thead>
                <tbody>{top_rows}</tbody>
            </table>
        </div>
    </div>

    <!-- Interactive Graph -->
    <div class="graph-section">
        <h3>Network Visualization</h3>
        <div id="graph-container"></div>
        <div class="legend" id="legend"></div>
    </div>
</div>

<script>
// Entity Type Chart
new Chart(document.getElementById('entityChart'), {{
    type: 'bar',
    data: {{
        labels: {entity_chart_labels},
        datasets: [{{ data: {entity_chart_values}, backgroundColor: {entity_chart_colors}, borderWidth: 0 }}]
    }},
    options: {{
        indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            x: {{ grid: {{ color: '#1e1e3f' }}, ticks: {{ color: '#8888aa' }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ color: '#e0e0e0', font: {{ size: 10 }} }} }}
        }}
    }}
}});

// Relation Type Chart
const relColors = ['#4fc3f7','#e94560','#4ecdc4','#ffeaa7','#a29bfe','#fd79a8','#00b894','#fdcb6e','#6c5ce7','#e17055','#81ecec','#55a3f0','#96ceb4','#d63031','#b2bec3'];
new Chart(document.getElementById('relChart'), {{
    type: 'bar',
    data: {{
        labels: {rel_chart_labels},
        datasets: [{{ data: {rel_chart_values}, backgroundColor: relColors, borderWidth: 0 }}]
    }},
    options: {{
        indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            x: {{ grid: {{ color: '#1e1e3f' }}, ticks: {{ color: '#8888aa' }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ color: '#e0e0e0', font: {{ size: 10 }} }} }}
        }}
    }}
}});

// Network Graph
const nodes = new vis.DataSet({json.dumps(nodes_json)});
const edges = new vis.DataSet({json.dumps(edges_json)});
const container = document.getElementById('graph-container');
const network = new vis.Network(container, {{ nodes, edges }}, {{
    physics: {{
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {{ gravitationalConstant: -80, centralGravity: 0.008, springLength: 120 }},
        stabilization: {{ iterations: 150 }}
    }},
    nodes: {{ shape: 'dot', borderWidth: 1, borderWidthSelected: 3, font: {{ size: 9, color: '#ccc' }} }},
    edges: {{ color: {{ color: '#333355', opacity: 0.4 }}, smooth: {{ type: 'continuous' }} }},
    interaction: {{ hover: true, tooltipDelay: 50 }}
}});

// Legend
const typeColors = {json.dumps(type_colors)};
const legendEl = document.getElementById('legend');
Object.entries(typeColors).forEach(([type, color]) => {{
    legendEl.innerHTML += `<div class="legend-item"><div class="legend-dot" style="background:${{color}}"></div>${{type}}</div>`;
}});
</script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate BioMedical KG analytics dashboard")
    parser.add_argument("--open", action="store_true", help="Open in browser after generation")
    args = parser.parse_args()

    print("=" * 60)
    print("GENERATING BIOMEDICAL KG ANALYTICS DASHBOARD")
    print("=" * 60)

    if not HAS_NETWORKX:
        print("ERROR: networkx is required. Install with: pip install networkx")
        return

    print("\nBuilding graph...")
    G, id_to_meta, rel_type_counter = build_graph()
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    print("\nComputing analytics (PageRank, components, density)...")
    analytics = compute_analytics(G)
    print(f"  Avg Degree: {analytics['avg_degree']}")
    print(f"  Components: {analytics['num_components']}")
    print(f"  Largest Component: {analytics['largest_pct']}%")

    print("\nGenerating dashboard HTML...")
    html = generate_dashboard_html(G, id_to_meta, rel_type_counter, analytics)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved to: {OUTPUT_PATH}")

    if args.open:
        import webbrowser
        webbrowser.open(str(OUTPUT_PATH))

    print(f"\n{'='*60}")
    print(f"DASHBOARD READY: {OUTPUT_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
