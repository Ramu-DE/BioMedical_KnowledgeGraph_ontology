"""
End-to-End Knwler Pipeline for BioMedical Knowledge Graph
==========================================================
Runs Knwler on biomedical documents and integrates the output into your KG.

Usage:
    # Single PDF
    python run_knwler_pipeline.py --file paper.pdf

    # Directory of PDFs
    python run_knwler_pipeline.py --directory ./papers/

    # Using OpenAI backend (better quality)
    python run_knwler_pipeline.py --file paper.pdf --backend openai

    # Using local Ollama (air-gapped, no data leaves machine)
    python run_knwler_pipeline.py --file paper.pdf --backend ollama

    # With custom biomedical schema (recommended for precision)
    python run_knwler_pipeline.py --file paper.pdf --use-schema

Prerequisites:
    pipx install knwler
    # For local: install Ollama + pull qwen2.5:3b
    # For cloud: set OPENAI_API_KEY environment variable
"""

import subprocess
import sys
import json
import os
import argparse
from pathlib import Path


# Biomedical-specific schema for Knwler extraction
# This improves precision by telling Knwler exactly what entity/relation types to look for
BIOMEDICAL_SCHEMA = {
    "entity_types": [
        "Drug",
        "Disease",
        "Gene",
        "Protein",
        "Biomarker",
        "Clinical_Trial",
        "Researcher",
        "Institution",
        "Adverse_Event",
        "Pathway",
        "Anatomy",
        "Cell_Type",
        "Biological_Process",
        "Molecular_Function",
        "Entity",
        "Exposure",
        "Phenotype",
        "Symptom",
    ],
    "relation_types": [
        "treats",
        "targets",
        "inhibits",
        "associated_with",
        "causes",
        "participates_in",
        "involved_in",
        "has_function",
        "expressed_in",
        "affects",
        "involves",
        "has_phenotype",
        "increases_risk",
        "predicts_response",
        "investigates",
        "studies",
        "reports",
        "sponsors",
        "authored_by",
        "mentions",
        "affiliated_with",
    ],
}


def run_knwler_extraction(
    input_path: str,
    output_dir: str,
    backend: str = "ollama",
    use_schema: bool = False,
    is_directory: bool = False,
) -> bool:
    """Run Knwler extraction on input document(s)."""

    cmd = ["knwler", "extract"]

    if is_directory:
        cmd.extend(["--directory", input_path])
    else:
        cmd.extend(["-f", input_path])

    cmd.extend(["--output", output_dir])
    cmd.extend(["--backend", backend])
    cmd.append("--overwrite")

    # If using custom schema, write it to a temp file and pass it
    if use_schema:
        schema_path = Path(output_dir) / "_biomedical_schema.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        with open(schema_path, "w") as f:
            json.dump(BIOMEDICAL_SCHEMA, f, indent=2)
        cmd.extend(["--schema", str(schema_path)])

    print(f"\n{'='*60}")
    print(f"STEP 1: Running Knwler extraction")
    print(f"  Input:   {input_path}")
    print(f"  Output:  {output_dir}")
    print(f"  Backend: {backend}")
    print(f"  Schema:  {'Biomedical (custom)' if use_schema else 'Auto-discovered'}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"ERROR: Knwler extraction failed:")
            print(result.stderr)
            return False
        print(result.stdout)
        return True
    except FileNotFoundError:
        print("ERROR: 'knwler' command not found. Install with: pipx install knwler")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: Knwler extraction timed out (>10 minutes)")
        return False


def run_integration(knwler_output_dir: str, nodes_dir: str, rel_dir: str, batch: bool = False) -> bool:
    """Run the integration script to map Knwler output to KG CSVs."""

    print(f"\n{'='*60}")
    print(f"STEP 2: Integrating into BioMedical Knowledge Graph")
    print(f"  Knwler output: {knwler_output_dir}")
    print(f"  Nodes dir:     {nodes_dir}")
    print(f"  Relations dir:  {rel_dir}")
    print(f"{'='*60}\n")

    script_dir = Path(__file__).parent
    integration_script = script_dir / "knwler_integration.py"

    cmd = [
        sys.executable,
        str(integration_script),
        "--input", knwler_output_dir,
        "--nodes-dir", nodes_dir,
        "--rel-dir", rel_dir,
        "--report", str(Path(knwler_output_dir) / "integration_report.txt"),
    ]

    if batch:
        cmd.append("--batch")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: Integration failed:")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end Knwler → BioMedical KG pipeline"
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", "-f", help="Path to a single document (PDF, MD, TXT)")
    input_group.add_argument("--directory", "--dir", help="Path to directory of documents")

    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai", "anthropic", "gemini", "lmstudio"],
                        help="LLM backend (default: ollama)")
    parser.add_argument("--use-schema", action="store_true",
                        help="Use predefined biomedical schema instead of auto-discovery")
    parser.add_argument("--output", default="./knwler_output",
                        help="Knwler output directory (default: ./knwler_output)")
    parser.add_argument("--nodes-dir", default=None,
                        help="Nodes CSV directory (default: auto-detect from project structure)")
    parser.add_argument("--rel-dir", default=None,
                        help="Relationships CSV directory (default: auto-detect from project structure)")

    args = parser.parse_args()

    # Auto-detect project directories
    script_dir = Path(__file__).parent.parent  # BioMedical_KnowledgeGraph/
    nodes_dir = args.nodes_dir or str(script_dir / "nodes")
    rel_dir = args.rel_dir or str(script_dir / "relationships")

    # Step 1: Extract with Knwler
    input_path = args.file or args.directory
    is_directory = args.directory is not None

    success = run_knwler_extraction(
        input_path=input_path,
        output_dir=args.output,
        backend=args.backend,
        use_schema=args.use_schema,
        is_directory=is_directory,
    )

    if not success:
        print("\nPipeline failed at extraction step.")
        sys.exit(1)

    # Step 2: Integrate into KG
    success = run_integration(
        knwler_output_dir=args.output,
        nodes_dir=nodes_dir,
        rel_dir=rel_dir,
        batch=is_directory,
    )

    if not success:
        print("\nPipeline failed at integration step.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"  New nodes/relationships appended to:")
    print(f"    {nodes_dir}/")
    print(f"    {rel_dir}/")
    print(f"  Knwler report: {args.output}/index.html")
    print(f"  Integration report: {args.output}/integration_report.txt")
    print(f"\n  Next step: Reload into Neo4j/Neptune using the Cypher script")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
