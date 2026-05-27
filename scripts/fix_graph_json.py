"""Convert graph.json to Knwler's expected internal format for HTML rendering."""

import json
from pathlib import Path

input_path = Path("BioMedical_KnowledgeGraph/visualization/graph.json")
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# If already in correct format, read from graph.entities at top level
entities = data.get("entities", [])
relations = data.get("relations", [])
clusters = data.get("clusters", [])

# Transform to Knwler's expected format:
# { title, summary, url, communities: [], chunks: [], graph: { entities: [], relations: [] } }
knwler_format = {
    "title": data.get("title", "BioMedical Knowledge Graph"),
    "summary": data.get("summary", ""),
    "url": "",
    "communities": [],
    "chunks": [],
    "graph": {
        "entities": [],
        "relations": relations,
    },
}

# Transform entities - add chunk_ids and community_id
for i, entity in enumerate(entities):
    knwler_format["graph"]["entities"].append({
        "name": entity["name"],
        "type": entity["type"],
        "description": entity.get("description", ""),
        "importance": entity.get("importance", 1.0),
        "chunk_ids": [0],
        "community_id": None,
    })

# Transform clusters to communities format
for i, cluster in enumerate(clusters):
    members = cluster.get("entities", [])
    topic = cluster.get("topic", f"Cluster {i}")

    # Assign community_id to entities that belong to this cluster
    for entity in knwler_format["graph"]["entities"]:
        if entity["name"] in members:
            entity["community_id"] = i

    knwler_format["communities"].append({
        "topics": [topic],
        "members": members,
        "description": f"Community cluster: {topic}",
    })

# Create a synthetic chunk so the template has something to render
summary_text = (
    f"BioMedical Knowledge Graph containing {len(entities)} entities "
    f"across 20 node types (Drug, Disease, Gene, Protein, Biomarker, "
    f"ClinicalTrial, Researcher, Institution, AdverseEvent, ResearchPaper, "
    f"Pathway, Anatomy, CellType, BiologicalProcess, MolecularFunction, "
    f"Entity, Exposure, Phenotype, Cluster, ClusterSummary) connected by "
    f"{len(relations)} relationships of 30 types."
)

knwler_format["chunks"] = [
    {
        "text": summary_text,
        "rephrase": summary_text,
    }
]

# Write the corrected format
with open(input_path, "w", encoding="utf-8") as f:
    json.dump(knwler_format, f, indent=2)

print(f"Converted to Knwler format:")
print(f"  Entities: {len(knwler_format['graph']['entities'])}")
print(f"  Relations: {len(knwler_format['graph']['relations'])}")
print(f"  Communities: {len(knwler_format['communities'])}")
print(f"  Chunks: {len(knwler_format['chunks'])}")
print(f"  Output: {input_path}")
