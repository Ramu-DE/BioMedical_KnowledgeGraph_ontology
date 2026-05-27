"""
Export BioMedical Knowledge Graph CSVs → Knwler graph.json
============================================================
Converts your existing node/relationship CSVs into Knwler's graph.json format,
then generates an interactive HTML visualization using Knwler's report engine.

Usage:
    # Generate graph.json + HTML visualization
    python export_to_knwler.py

    # Specify output directory
    python export_to_knwler.py --output ./visualization

    # Then open the HTML report in your browser
    # Or use: knwler extract --html-only --output ./visualization

Prerequisites:
    pipx install knwler
"""

import csv
import json
import argparse
import subprocess
import sys
from pathlib import Path


def load_csv(filepath: Path) -> list[dict]:
    """Load a CSV file into a list of dictionaries."""
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_graph_json(nodes_dir: Path, relationships_dir: Path) -> dict:
    """
    Convert all BioMedical KG CSVs into Knwler's graph.json format.
    
    Knwler graph.json structure:
    {
        "entities": [{"name": str, "type": str, "description": str, "importance": float}],
        "relations": [{"source": str, "target": str, "type": str, "description": str, "strength": float}],
        "clusters": [{"topic": str, "entities": [str]}],
        "title": str,
        "summary": str
    }
    """
    entities = []
    entity_id_to_name = {}  # Maps IDs to names for relationship resolution

    # Node file configurations: (filename, id_field, type_label, description_fields)
    node_configs = [
        ("drugs.csv", "drug_id", "Drug", ["mechanism", "drug_type"]),
        ("diseases.csv", "disease_id", "Disease", ["category", "prevalence"]),
        ("genes.csv", "gene_id", "Gene", ["function", "chromosome"]),
        ("proteins.csv", "protein_id", "Protein", ["protein_class", "cellular_location"]),
        ("biomarkers.csv", "biomarker_id", "Biomarker", ["type", "clinical_significance"]),
        ("clinical_trials.csv", "trial_id", "ClinicalTrial", ["phase", "status"]),
        ("researchers.csv", "researcher_id", "Researcher", ["specialization", "title"]),
        ("institutions.csv", "institution_id", "Institution", ["type", "country"]),
        ("adverse_events.csv", "event_id", "AdverseEvent", ["severity", "category"]),
        ("research_papers.csv", "paper_id", "ResearchPaper", ["journal", "publication_date"]),
        ("pathways.csv", "pathway_id", "Pathway", ["category", "organism"]),
        ("anatomy.csv", "anatomy_id", "Anatomy", ["system", "description"]),
        ("cell_types.csv", "cell_type_id", "CellType", ["category", "location"]),
        ("biological_processes.csv", "process_id", "BiologicalProcess", ["category", "description"]),
        ("molecular_functions.csv", "function_id", "MolecularFunction", ["category", "description"]),
        ("entities.csv", "entity_id", "Entity", ["entity_type", "description"]),
        ("exposures.csv", "exposure_id", "Exposure", ["exposure_type", "risk_level"]),
        ("phenotypes.csv", "phenotype_id", "Phenotype", ["category", "description"]),
        ("clusters.csv", "cluster_id", "Cluster", ["cluster_type", "algorithm"]),
        ("cluster_summaries.csv", "summary_id", "ClusterSummary", ["therapeutic_relevance", "summary_text"]),
    ]

    # Load all nodes
    for filename, id_field, type_label, desc_fields in node_configs:
        rows = load_csv(nodes_dir / filename)
        for row in rows:
            node_id = row.get(id_field, "")
            name = row.get("name", row.get("title", row.get("symbol", "")))
            
            # Build description from available fields
            desc_parts = []
            for field in desc_fields:
                val = row.get(field, "")
                if val:
                    desc_parts.append(f"{field}: {val}")
            description = "; ".join(desc_parts)

            entity_id_to_name[node_id] = name

            entities.append({
                "name": name,
                "type": type_label,
                "description": description,
                "importance": 1.0,
            })

    # Load all relationships
    relations = []

    # Relationship file configurations: (filename, source_id_field, target_id_field, rel_type, desc_fields)
    rel_configs = [
        ("drug_treats_disease.csv", "drug_id", "disease_id", "TREATS", ["efficacy_rate"]),
        ("drug_targets_protein.csv", "drug_id", "protein_id", "TARGETS", ["mechanism_type", "binding_affinity"]),
        ("gene_associated_with_disease.csv", "gene_id", "disease_id", "ASSOCIATED_WITH", ["association_strength", "evidence_level"]),
        ("biomarker_predicts_response.csv", "biomarker_id", "drug_id", "PREDICTS_RESPONSE", ["predictive_value"]),
        ("trial_investigates_drug.csv", "trial_id", "drug_id", "INVESTIGATES", ["dosage"]),
        ("trial_studies_disease.csv", "trial_id", "disease_id", "STUDIES", ["patient_population"]),
        ("trial_reports_adverse_event.csv", "trial_id", "event_id", "REPORTS", ["incidence_rate"]),
        ("institution_sponsors_trial.csv", "institution_id", "trial_id", "SPONSORS", ["funding_amount_millions"]),
        ("paper_authored_by.csv", "paper_id", "researcher_id", "AUTHORED_BY", ["author_position"]),
        ("paper_mentions_disease.csv", "paper_id", "disease_id", "MENTIONS", ["mention_count"]),
        ("paper_mentions_drug.csv", "paper_id", "drug_id", "MENTIONS", ["mention_count"]),
        ("researcher_affiliated_with.csv", "researcher_id", "institution_id", "AFFILIATED_WITH", ["role"]),
        ("gene_participates_in_pathway.csv", "gene_id", "pathway_id", "PARTICIPATES_IN", ["role"]),
        ("protein_involved_in_pathway.csv", "protein_id", "pathway_id", "INVOLVED_IN", ["role"]),
        ("pathway_involves_biological_process.csv", "pathway_id", "process_id", "REGULATES", ["relationship"]),
        ("gene_involved_in_biological_process.csv", "gene_id", "process_id", "INVOLVED_IN", ["evidence_code"]),
        ("protein_involved_in_biological_process.csv", "protein_id", "process_id", "INVOLVED_IN", ["evidence_code"]),
        ("gene_has_molecular_function.csv", "gene_id", "function_id", "HAS_FUNCTION", ["evidence_code"]),
        ("protein_has_molecular_function.csv", "protein_id", "function_id", "HAS_FUNCTION", ["evidence_code"]),
        ("protein_expressed_in_anatomy.csv", "protein_id", "anatomy_id", "EXPRESSED_IN", ["expression_level"]),
        ("disease_affects_anatomy.csv", "disease_id", "anatomy_id", "AFFECTS", ["severity"]),
        ("cell_type_found_in_anatomy.csv", "cell_type_id", "anatomy_id", "FOUND_IN", ["abundance"]),
        ("disease_involves_cell_type.csv", "disease_id", "cell_type_id", "INVOLVES", ["involvement_type"]),
        ("cluster_has_summary.csv", "cluster_id", "summary_id", "HAS_SUMMARY", []),
        ("disease_has_phenotype.csv", "disease_id", "phenotype_id", "HAS_PHENOTYPE", ["frequency", "severity"]),
        ("exposure_increases_risk_disease.csv", "exposure_id", "disease_id", "INCREASES_RISK", ["relative_risk", "mechanism"]),
        ("exposure_affects_gene.csv", "exposure_id", "gene_id", "AFFECTS", ["effect_type", "mechanism"]),
        ("entity_associated_with_disease.csv", "entity_id", "disease_id", "ASSOCIATED_WITH", ["association_type"]),
        ("phenotype_associated_with_gene.csv", "phenotype_id", "gene_id", "ASSOCIATED_WITH", ["association_type"]),
        ("node_belongs_to_cluster.csv", "node_id", "cluster_id", "BELONGS_TO", ["membership_score"]),
    ]

    for filename, src_field, tgt_field, rel_type, desc_fields in rel_configs:
        rows = load_csv(relationships_dir / filename)
        for row in rows:
            src_id = row.get(src_field, "")
            tgt_id = row.get(tgt_field, "")
            src_name = entity_id_to_name.get(src_id, src_id)
            tgt_name = entity_id_to_name.get(tgt_id, tgt_id)

            # Build description
            desc_parts = []
            for field in desc_fields:
                val = row.get(field, "")
                if val:
                    desc_parts.append(f"{field}: {val}")
            description = "; ".join(desc_parts)

            # Calculate strength from available numeric fields
            strength = 1.0
            for field in desc_fields:
                val = row.get(field, "")
                try:
                    numeric_val = float(val)
                    if 0 <= numeric_val <= 1:
                        strength = numeric_val
                        break
                except (ValueError, TypeError):
                    pass

            relations.append({
                "source": src_name,
                "target": tgt_name,
                "type": rel_type,
                "description": description,
                "strength": strength,
            })

    # Build clusters from clusters.csv + node_belongs_to_cluster.csv
    clusters_data = []
    cluster_rows = load_csv(nodes_dir / "clusters.csv")
    membership_rows = load_csv(relationships_dir / "node_belongs_to_cluster.csv")

    for cluster_row in cluster_rows:
        cluster_id = cluster_row.get("cluster_id", "")
        cluster_name = cluster_row.get("name", "")
        
        # Find members
        members = []
        for mem_row in membership_rows:
            if mem_row.get("cluster_id") == cluster_id:
                node_id = mem_row.get("node_id", "")
                node_name = entity_id_to_name.get(node_id, node_id)
                members.append(node_name)

        clusters_data.append({
            "topic": cluster_name,
            "entities": members,
        })

    # Assemble final graph.json
    graph = {
        "title": "BioMedical Knowledge Graph",
        "summary": (
            "A comprehensive biomedical knowledge graph with 20 node types and 30 relationship types, "
            "covering drugs, diseases, genes, proteins, pathways, clinical trials, and more. "
            "Built for GraphRAG-powered biomedical question answering."
        ),
        "entities": entities,
        "relations": relations,
        "clusters": clusters_data,
        "language": "en",
    }

    return graph


def generate_html_report(graph_json_path: Path, output_dir: Path) -> bool:
    """Use Knwler to generate an interactive HTML report from graph.json."""
    
    # Try using knwler's html-only mode
    cmd = [
        "knwler", "extract",
        "--html-only",
        "--output", str(output_dir),
    ]

    print(f"\nGenerating HTML visualization...")
    print(f"  Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(output_dir))
        if result.returncode == 0:
            print(f"  HTML report generated at: {output_dir / 'index.html'}")
            return True
        else:
            print(f"  Knwler HTML generation returned error, trying fallback...")
            return False
    except FileNotFoundError:
        print("  'knwler' not found, generating standalone HTML instead...")
        return False


def generate_standalone_html(graph: dict, output_dir: Path):
    """Generate a standalone HTML visualization without requiring Knwler CLI."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioMedical Knowledge Graph - Interactive Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/vis-network.min.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; }}
        .header {{ padding: 20px 30px; background: #16213e; border-bottom: 1px solid #0f3460; }}
        .header h1 {{ font-size: 1.5rem; color: #e94560; }}
        .header p {{ font-size: 0.9rem; color: #aaa; margin-top: 5px; }}
        .container {{ display: flex; height: calc(100vh - 80px); }}
        #graph {{ flex: 1; background: #0f0f23; }}
        .sidebar {{ width: 320px; background: #16213e; padding: 20px; overflow-y: auto; border-left: 1px solid #0f3460; }}
        .sidebar h2 {{ font-size: 1.1rem; color: #e94560; margin-bottom: 15px; }}
        .stat {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #0f3460; }}
        .stat-label {{ color: #aaa; }}
        .stat-value {{ color: #fff; font-weight: bold; }}
        .legend {{ margin-top: 20px; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; padding: 4px 0; }}
        .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
        .controls {{ margin-top: 20px; }}
        .controls label {{ display: block; color: #aaa; margin-bottom: 5px; font-size: 0.85rem; }}
        .controls input[type="range"] {{ width: 100%; }}
        .filter-btn {{ padding: 4px 10px; margin: 2px; border: 1px solid #0f3460; background: #1a1a2e; color: #aaa; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }}
        .filter-btn.active {{ background: #e94560; color: #fff; border-color: #e94560; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BioMedical Knowledge Graph</h1>
        <p>{len(graph['entities'])} entities &middot; {len(graph['relations'])} relationships &middot; {len(graph['clusters'])} clusters</p>
    </div>
    <div class="container">
        <div id="graph"></div>
        <div class="sidebar">
            <h2>Graph Statistics</h2>
            <div class="stat"><span class="stat-label">Nodes</span><span class="stat-value">{len(graph['entities'])}</span></div>
            <div class="stat"><span class="stat-label">Edges</span><span class="stat-value">{len(graph['relations'])}</span></div>
            <div class="stat"><span class="stat-label">Clusters</span><span class="stat-value">{len(graph['clusters'])}</span></div>
            <div class="stat"><span class="stat-label">Node Types</span><span class="stat-value">{len(set(e['type'] for e in graph['entities']))}</span></div>
            <div class="stat"><span class="stat-label">Edge Types</span><span class="stat-value">{len(set(r['type'] for r in graph['relations']))}</span></div>

            <div class="controls">
                <label>Min connections to show:</label>
                <input type="range" id="degreeSlider" min="0" max="10" value="0" oninput="filterByDegree(this.value)">
                <span id="degreeValue">0</span>
            </div>

            <h2 style="margin-top:20px;">Node Types</h2>
            <div id="filters"></div>

            <div class="legend" id="legend"></div>
        </div>
    </div>

    <script>
    const graphData = {json.dumps(graph, indent=None)};

    const typeColors = {{
        'Drug': '#e94560',
        'Disease': '#ff6b6b',
        'Gene': '#4ecdc4',
        'Protein': '#45b7d1',
        'Biomarker': '#96ceb4',
        'ClinicalTrial': '#ffeaa7',
        'Researcher': '#dfe6e9',
        'Institution': '#a29bfe',
        'AdverseEvent': '#fd79a8',
        'ResearchPaper': '#81ecec',
        'Pathway': '#55a3f0',
        'Anatomy': '#00b894',
        'CellType': '#6c5ce7',
        'BiologicalProcess': '#fdcb6e',
        'MolecularFunction': '#e17055',
        'Entity': '#636e72',
        'Exposure': '#d63031',
        'Phenotype': '#e84393',
        'Cluster': '#2d3436',
        'ClusterSummary': '#b2bec3',
    }};

    // Build vis.js nodes and edges
    const nodes = graphData.entities.map((e, i) => ({{
        id: i,
        label: e.name,
        title: `${{e.type}}\\n${{e.description}}`,
        group: e.type,
        color: typeColors[e.type] || '#666',
        font: {{ color: '#fff', size: 11 }},
    }}));

    const nameToId = {{}};
    graphData.entities.forEach((e, i) => {{ nameToId[e.name] = i; }});

    const edges = graphData.relations
        .filter(r => nameToId[r.source] !== undefined && nameToId[r.target] !== undefined)
        .map(r => ({{
            from: nameToId[r.source],
            to: nameToId[r.target],
            label: r.type,
            title: r.description,
            arrows: 'to',
            color: {{ color: '#555', opacity: 0.6 }},
            font: {{ color: '#888', size: 9 }},
        }}));

    const container = document.getElementById('graph');
    const data = {{ nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }};
    const options = {{
        physics: {{
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {{ gravitationalConstant: -50, centralGravity: 0.005, springLength: 150 }},
            stabilization: {{ iterations: 200 }},
        }},
        interaction: {{ hover: true, tooltipDelay: 100 }},
        nodes: {{ shape: 'dot', size: 16, borderWidth: 2 }},
        edges: {{ smooth: {{ type: 'continuous' }} }},
    }};

    const network = new vis.Network(container, data, options);

    // Build legend and filters
    const types = [...new Set(graphData.entities.map(e => e.type))].sort();
    const legendEl = document.getElementById('legend');
    const filtersEl = document.getElementById('filters');

    types.forEach(t => {{
        const count = graphData.entities.filter(e => e.type === t).length;
        legendEl.innerHTML += `<div class="legend-item"><div class="legend-dot" style="background:${{typeColors[t] || '#666'}}"></div><span>${{t}} (${{count}})</span></div>`;
        filtersEl.innerHTML += `<button class="filter-btn active" onclick="toggleType('${{t}}', this)">${{t}}</button>`;
    }});

    let activeTypes = new Set(types);

    function toggleType(type, btn) {{
        if (activeTypes.has(type)) {{
            activeTypes.delete(type);
            btn.classList.remove('active');
        }} else {{
            activeTypes.add(type);
            btn.classList.add('active');
        }}
        applyFilters();
    }}

    function filterByDegree(val) {{
        document.getElementById('degreeValue').textContent = val;
        applyFilters();
    }}

    function applyFilters() {{
        const minDegree = parseInt(document.getElementById('degreeSlider').value);
        const visibleNodes = nodes.filter(n => {{
            if (!activeTypes.has(n.group)) return false;
            const degree = edges.filter(e => e.from === n.id || e.to === n.id).length;
            return degree >= minDegree;
        }}).map(n => n.id);

        data.nodes.forEach(n => {{
            data.nodes.update({{ id: n.id, hidden: !visibleNodes.includes(n.id) }});
        }});
    }}
    </script>
</body>
</html>"""

    output_file = output_dir / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n  Standalone HTML visualization generated: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Export BioMedical KG to Knwler graph.json and generate visualization"
    )
    parser.add_argument("--output", "-o", default="./visualization",
                        help="Output directory (default: ./visualization)")
    parser.add_argument("--nodes-dir", default=None,
                        help="Nodes CSV directory (default: auto-detect)")
    parser.add_argument("--rel-dir", default=None,
                        help="Relationships CSV directory (default: auto-detect)")
    parser.add_argument("--open", action="store_true",
                        help="Open HTML report in browser after generation")

    args = parser.parse_args()

    # Auto-detect directories
    script_dir = Path(__file__).parent.parent  # BioMedical_KnowledgeGraph/
    nodes_dir = Path(args.nodes_dir) if args.nodes_dir else script_dir / "nodes"
    rel_dir = Path(args.rel_dir) if args.rel_dir else script_dir / "relationships"
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BIOMEDICAL KG → KNWLER VISUALIZATION EXPORT")
    print("=" * 60)
    print(f"  Nodes dir:   {nodes_dir}")
    print(f"  Rels dir:    {rel_dir}")
    print(f"  Output dir:  {output_dir}")

    # Build graph.json
    print("\nBuilding graph.json from CSVs...")
    graph = build_graph_json(nodes_dir, rel_dir)

    # Write graph.json
    graph_json_path = output_dir / "graph.json"
    with open(graph_json_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    print(f"  graph.json written: {graph_json_path}")
    print(f"    Entities:      {len(graph['entities'])}")
    print(f"    Relations:      {len(graph['relations'])}")
    print(f"    Clusters:       {len(graph['clusters'])}")

    # Try Knwler HTML generation first, fall back to standalone
    success = generate_html_report(graph_json_path, output_dir)
    if not success:
        html_path = generate_standalone_html(graph, output_dir)

    # Open in browser if requested
    if args.open:
        import webbrowser
        html_file = output_dir / "index.html"
        if html_file.exists():
            webbrowser.open(str(html_file))

    print(f"\n{'='*60}")
    print("DONE! Open the visualization:")
    print(f"  {output_dir / 'index.html'}")
    print(f"\nOr use Knwler's graph analysis:")
    print(f"  knwler graph analyze {graph_json_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
