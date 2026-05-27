# Knwler Integration for BioMedical Knowledge Graph

## Overview

This integration connects [Knwler](https://knwler.com/) (open-source document intelligence) with your BioMedical Knowledge Graph. It automatically extracts entities and relationships from biomedical PDFs and maps them into your existing 20-node-type, 30-relationship-type schema.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Biomedical Documents (PDFs, papers, reports)            │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Knwler (LLM-powered extraction)                         │
│  • Auto schema discovery OR custom biomedical schema     │
│  • Entity extraction (drugs, genes, diseases, etc.)      │
│  • Relationship extraction                               │
│  • Community detection (clusters)                        │
│  Output: graph.json                                      │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  knwler_integration.py (this script)                     │
│  • Maps Knwler types → BioMedical KG ontology            │
│  • Deduplicates against existing nodes                   │
│  • Generates sequential IDs (D011, DIS011, etc.)         │
│  • Appends to existing CSVs                              │
│  Output: Updated nodes/*.csv + relationships/*.csv       │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Neo4j / Neptune (graph database)                        │
│  Load with neo4j_load_complete_graph.cypher              │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Install Knwler
pipx install knwler

# For local LLM (no data leaves your machine):
# Install Ollama: https://ollama.ai
ollama pull qwen2.5:3b

# For cloud LLM (better quality):
export OPENAI_API_KEY="your_key_here"
```

## Quick Start

### Option 1: One-command pipeline

```bash
cd BioMedical_KnowledgeGraph/scripts

# Process a single paper (local LLM)
python run_knwler_pipeline.py --file ../papers/research_paper.pdf

# Process with OpenAI (better extraction quality)
python run_knwler_pipeline.py --file ../papers/research_paper.pdf --backend openai

# Process a directory of papers
python run_knwler_pipeline.py --directory ../papers/ --backend openai

# Use custom biomedical schema (recommended for precision)
python run_knwler_pipeline.py --file paper.pdf --backend openai --use-schema
```

### Option 2: Step by step

```bash
# Step 1: Run Knwler extraction
knwler -f paper.pdf --backend openai --output ./knwler_output

# Step 2: Integrate into KG CSVs
python knwler_integration.py --input ./knwler_output/graph.json \
    --nodes-dir ../nodes \
    --rel-dir ../relationships

# Step 3: Reload into Neo4j
# Run neo4j_load_complete_graph.cypher in Neo4j Browser
```

## Entity Type Mapping

Knwler auto-discovers entity types from documents. The integration maps them to your schema:

| Knwler Type | → | KG Node Type |
|---|---|---|
| drug, medication, compound | → | Drug |
| disease, condition, cancer | → | Disease |
| gene, oncogene | → | Gene |
| protein, enzyme, receptor | → | Protein |
| biomarker, marker | → | Biomarker |
| clinical_trial, study | → | ClinicalTrial |
| pathway, signaling_pathway | → | Pathway |
| organ, tissue, anatomy | → | Anatomy |
| cell, cell_type | → | CellType |
| symptom, phenotype | → | Phenotype |
| exposure, risk_factor | → | Exposure |
| organism, pathogen, virus | → | Entity |

## Custom Schema Mode

By default, Knwler auto-discovers entity types. For biomedical documents, using `--use-schema` provides a predefined biomedical ontology that improves precision:

```bash
python run_knwler_pipeline.py --file paper.pdf --use-schema
```

This tells Knwler to look specifically for drugs, genes, diseases, proteins, pathways, etc. rather than discovering generic types.

## Deduplication

The integration script:
1. Loads all existing node CSVs on startup
2. Builds a name→ID index
3. When Knwler extracts "Pembrolizumab" and it already exists as D001, it reuses D001
4. Only creates new nodes for genuinely new entities

## Batch Processing

For large document sets, use Knwler's batch API to reduce cost:

```bash
# Uses OpenAI batch API (50% cheaper, async)
knwler batch run --input ./papers/ --output ./results/ --backend openai

# After batch completes, integrate all results
python knwler_integration.py --input ./results/ --batch \
    --nodes-dir ../nodes --rel-dir ../relationships
```

## Output

After running the pipeline:
- **New nodes** are appended to existing CSV files in `nodes/`
- **New relationships** are appended to existing CSV files in `relationships/`
- **Integration report** shows mapping statistics and any unmapped types
- **Knwler HTML report** provides interactive visualization of the extracted graph

## Extending the Mapping

If Knwler discovers entity types not in the current mapping, the integration report will list them under "UNMAPPED ENTITY TYPES". To add support:

1. Open `knwler_integration.py`
2. Add entries to `ENTITY_TYPE_MAP` dictionary
3. Re-run the integration

## Air-Gapped Operation

For sensitive biomedical data that cannot leave your network:

```bash
# Use Ollama (fully local, no API calls)
python run_knwler_pipeline.py --file sensitive_trial_data.pdf --backend ollama

# Or LM Studio
python run_knwler_pipeline.py --file sensitive_trial_data.pdf --backend lmstudio
```

Zero data leaves your infrastructure.
