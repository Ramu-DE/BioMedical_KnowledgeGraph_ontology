// ============================================================
// BIOMEDICAL KNOWLEDGE GRAPH - COMPLETE NEO4J LOAD SCRIPT
// ============================================================
// This script creates a full biomedical knowledge graph with:
//   20 Node Types, 30 Relationship Types
// Matching the schema visualization pattern from Neo4j Browser
// ============================================================

// ============================================================
// STEP 1: CREATE CONSTRAINTS & INDEXES
// ============================================================

CREATE CONSTRAINT FOR (d:Drug) REQUIRE d.drug_id IS UNIQUE;
CREATE CONSTRAINT FOR (dis:Disease) REQUIRE dis.disease_id IS UNIQUE;
CREATE CONSTRAINT FOR (g:Gene) REQUIRE g.gene_id IS UNIQUE;
CREATE CONSTRAINT FOR (p:Protein) REQUIRE p.protein_id IS UNIQUE;
CREATE CONSTRAINT FOR (b:Biomarker) REQUIRE b.biomarker_id IS UNIQUE;
CREATE CONSTRAINT FOR (ct:ClinicalTrial) REQUIRE ct.trial_id IS UNIQUE;
CREATE CONSTRAINT FOR (r:Researcher) REQUIRE r.researcher_id IS UNIQUE;
CREATE CONSTRAINT FOR (i:Institution) REQUIRE i.institution_id IS UNIQUE;
CREATE CONSTRAINT FOR (ae:AdverseEvent) REQUIRE ae.event_id IS UNIQUE;
CREATE CONSTRAINT FOR (rp:ResearchPaper) REQUIRE rp.paper_id IS UNIQUE;
CREATE CONSTRAINT FOR (pw:Pathway) REQUIRE pw.pathway_id IS UNIQUE;
CREATE CONSTRAINT FOR (an:Anatomy) REQUIRE an.anatomy_id IS UNIQUE;
CREATE CONSTRAINT FOR (ctype:CellType) REQUIRE ctype.cell_type_id IS UNIQUE;
CREATE CONSTRAINT FOR (bp:BiologicalProcess) REQUIRE bp.process_id IS UNIQUE;
CREATE CONSTRAINT FOR (mf:MolecularFunction) REQUIRE mf.function_id IS UNIQUE;
CREATE CONSTRAINT FOR (ent:Entity) REQUIRE ent.entity_id IS UNIQUE;
CREATE CONSTRAINT FOR (exp:Exposure) REQUIRE exp.exposure_id IS UNIQUE;
CREATE CONSTRAINT FOR (phe:Phenotype) REQUIRE phe.phenotype_id IS UNIQUE;
CREATE CONSTRAINT FOR (clu:Cluster) REQUIRE clu.cluster_id IS UNIQUE;
CREATE CONSTRAINT FOR (cs:ClusterSummary) REQUIRE cs.summary_id IS UNIQUE;

// ============================================================
// STEP 2: LOAD NODES
// ============================================================

// --- Drugs ---
LOAD CSV WITH HEADERS FROM 'file:///drugs.csv' AS row
CREATE (d:Drug {
  drug_id: row.drug_id,
  name: row.name,
  generic_name: row.generic_name,
  drug_type: row.drug_type,
  approval_status: row.approval_status,
  approval_year: toInteger(row.approval_year),
  mechanism: row.mechanism
});

// --- Diseases ---
LOAD CSV WITH HEADERS FROM 'file:///diseases.csv' AS row
CREATE (dis:Disease {
  disease_id: row.disease_id,
  name: row.name,
  category: row.category,
  icd10_code: row.icd10_code,
  prevalence: row.prevalence
});

// --- Genes ---
LOAD CSV WITH HEADERS FROM 'file:///genes.csv' AS row
CREATE (g:Gene {
  gene_id: row.gene_id,
  symbol: row.symbol,
  name: row.name,
  chromosome: row.chromosome,
  function: row.function
});

// --- Proteins ---
LOAD CSV WITH HEADERS FROM 'file:///proteins.csv' AS row
CREATE (p:Protein {
  protein_id: row.protein_id,
  name: row.name,
  uniprot_id: row.uniprot_id,
  protein_class: row.protein_class,
  cellular_location: row.cellular_location
});

// --- Biomarkers ---
LOAD CSV WITH HEADERS FROM 'file:///biomarkers.csv' AS row
CREATE (b:Biomarker {
  biomarker_id: row.biomarker_id,
  name: row.name,
  type: row.type,
  measurement_unit: row.measurement_unit,
  clinical_significance: row.clinical_significance
});

// --- Clinical Trials ---
LOAD CSV WITH HEADERS FROM 'file:///clinical_trials.csv' AS row
CREATE (ct:ClinicalTrial {
  trial_id: row.trial_id,
  nct_id: row.nct_id,
  title: row.title,
  phase: row.phase,
  status: row.status,
  start_date: row.start_date,
  enrollment: toInteger(row.enrollment),
  sponsor: row.sponsor
});

// --- Researchers ---
LOAD CSV WITH HEADERS FROM 'file:///researchers.csv' AS row
CREATE (r:Researcher {
  researcher_id: row.researcher_id,
  name: row.name,
  title: row.title,
  specialization: row.specialization,
  h_index: toInteger(row.h_index),
  total_publications: toInteger(row.total_publications)
});

// --- Institutions ---
LOAD CSV WITH HEADERS FROM 'file:///institutions.csv' AS row
CREATE (i:Institution {
  institution_id: row.institution_id,
  name: row.name,
  type: row.type,
  country: row.country,
  city: row.city,
  research_budget_millions: toFloat(row.research_budget_millions)
});

// --- Adverse Events ---
LOAD CSV WITH HEADERS FROM 'file:///adverse_events.csv' AS row
CREATE (ae:AdverseEvent {
  event_id: row.event_id,
  name: row.name,
  severity: row.severity,
  category: row.category,
  frequency: row.frequency
});

// --- Research Papers ---
LOAD CSV WITH HEADERS FROM 'file:///research_papers.csv' AS row
CREATE (rp:ResearchPaper {
  paper_id: row.paper_id,
  title: row.title,
  journal: row.journal,
  publication_date: row.publication_date,
  doi: row.doi,
  citations: toInteger(row.citations)
});

// --- Pathways (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///pathways.csv' AS row
CREATE (pw:Pathway {
  pathway_id: row.pathway_id,
  name: row.name,
  kegg_id: row.kegg_id,
  category: row.category,
  organism: row.organism
});

// --- Anatomy (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///anatomy.csv' AS row
CREATE (an:Anatomy {
  anatomy_id: row.anatomy_id,
  name: row.name,
  uberon_id: row.uberon_id,
  system: row.system,
  description: row.description
});

// --- Cell Types (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///cell_types.csv' AS row
CREATE (ctype:CellType {
  cell_type_id: row.cell_type_id,
  name: row.name,
  cell_ontology_id: row.cell_ontology_id,
  category: row.category,
  location: row.location
});

// --- Biological Processes (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///biological_processes.csv' AS row
CREATE (bp:BiologicalProcess {
  process_id: row.process_id,
  name: row.name,
  go_id: row.go_id,
  category: row.category,
  description: row.description
});

// --- Molecular Functions (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///molecular_functions.csv' AS row
CREATE (mf:MolecularFunction {
  function_id: row.function_id,
  name: row.name,
  go_id: row.go_id,
  category: row.category,
  description: row.description
});

// --- Entities (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///entities.csv' AS row
CREATE (ent:Entity {
  entity_id: row.entity_id,
  name: row.name,
  entity_type: row.entity_type,
  source: row.source,
  description: row.description
});

// --- Exposures (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///exposures.csv' AS row
CREATE (exp:Exposure {
  exposure_id: row.exposure_id,
  name: row.name,
  exposure_type: row.exposure_type,
  category: row.category,
  risk_level: row.risk_level,
  source: row.source
});

// --- Phenotypes (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///phenotypes.csv' AS row
CREATE (phe:Phenotype {
  phenotype_id: row.phenotype_id,
  name: row.name,
  hpo_id: row.hpo_id,
  category: row.category,
  description: row.description
});

// --- Clusters (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///clusters.csv' AS row
CREATE (clu:Cluster {
  cluster_id: row.cluster_id,
  name: row.name,
  cluster_type: row.cluster_type,
  algorithm: row.algorithm,
  node_count: toInteger(row.node_count),
  description: row.description
});

// --- Cluster Summaries (NEW) ---
LOAD CSV WITH HEADERS FROM 'file:///cluster_summaries.csv' AS row
CREATE (cs:ClusterSummary {
  summary_id: row.summary_id,
  cluster_id: row.cluster_id,
  summary_text: row.summary_text,
  key_entities: row.key_entities,
  therapeutic_relevance: row.therapeutic_relevance,
  confidence_score: toFloat(row.confidence_score)
});

// ============================================================
// STEP 3: LOAD RELATIONSHIPS (ORIGINAL)
// ============================================================

// Drug -[TREATS]-> Disease
LOAD CSV WITH HEADERS FROM 'file:///relationships/drug_treats_disease.csv' AS row
MATCH (d:Drug {drug_id: row.drug_id})
MATCH (dis:Disease {disease_id: row.disease_id})
CREATE (d)-[:TREATS {efficacy_rate: toFloat(row.efficacy_rate), approval_year: toInteger(row.approval_year)}]->(dis);

// Drug -[TARGETS]-> Protein
LOAD CSV WITH HEADERS FROM 'file:///relationships/drug_targets_protein.csv' AS row
MATCH (d:Drug {drug_id: row.drug_id})
MATCH (p:Protein {protein_id: row.protein_id})
CREATE (d)-[:TARGETS {binding_affinity: row.binding_affinity, mechanism_type: row.mechanism_type}]->(p);

// Gene -[ASSOCIATED_WITH]-> Disease
LOAD CSV WITH HEADERS FROM 'file:///relationships/gene_associated_with_disease.csv' AS row
MATCH (g:Gene {gene_id: row.gene_id})
MATCH (dis:Disease {disease_id: row.disease_id})
CREATE (g)-[:ASSOCIATED_WITH {association_strength: row.association_strength, evidence_level: row.evidence_level}]->(dis);

// Biomarker -[PREDICTS_RESPONSE]-> Drug
LOAD CSV WITH HEADERS FROM 'file:///relationships/biomarker_predicts_response.csv' AS row
MATCH (b:Biomarker {biomarker_id: row.biomarker_id})
MATCH (d:Drug {drug_id: row.drug_id})
CREATE (b)-[:PREDICTS_RESPONSE {predictive_value: toFloat(row.predictive_value), threshold: row.threshold}]->(d);

// ClinicalTrial -[INVESTIGATES]-> Drug
LOAD CSV WITH HEADERS FROM 'file:///relationships/trial_investigates_drug.csv' AS row
MATCH (ct:ClinicalTrial {trial_id: row.trial_id})
MATCH (d:Drug {drug_id: row.drug_id})
CREATE (ct)-[:INVESTIGATES {arm_type: row.arm_type, dosage: row.dosage}]->(d);

// ClinicalTrial -[STUDIES]-> Disease
LOAD CSV WITH HEADERS FROM 'file:///relationships/trial_studies_disease.csv' AS row
MATCH (ct:ClinicalTrial {trial_id: row.trial_id})
MATCH (dis:Disease {disease_id: row.disease_id})
CREATE (ct)-[:STUDIES {patient_population: row.patient_population}]->(dis);

// ClinicalTrial -[REPORTS]-> AdverseEvent
LOAD CSV WITH HEADERS FROM 'file:///relationships/trial_reports_adverse_event.csv' AS row
MATCH (ct:ClinicalTrial {trial_id: row.trial_id})
MATCH (ae:AdverseEvent {event_id: row.event_id})
CREATE (ct)-[:REPORTS {incidence_rate: toFloat(row.incidence_rate), grade: toInteger(row.grade)}]->(ae);

// Institution -[SPONSORS]-> ClinicalTrial
LOAD CSV WITH HEADERS FROM 'file:///relationships/institution_sponsors_trial.csv' AS row
MATCH (i:Institution {institution_id: row.institution_id})
MATCH (ct:ClinicalTrial {trial_id: row.trial_id})
CREATE (i)-[:SPONSORS {funding_amount_millions: toFloat(row.funding_amount_millions), role: row.role}]->(ct);

// ResearchPaper -[AUTHORED_BY]-> Researcher
LOAD CSV WITH HEADERS FROM 'file:///relationships/paper_authored_by.csv' AS row
MATCH (rp:ResearchPaper {paper_id: row.paper_id})
MATCH (r:Researcher {researcher_id: row.researcher_id})
CREATE (rp)-[:AUTHORED_BY {author_position: row.author_position}]->(r);

// ResearchPaper -[MENTIONS]-> Disease
LOAD CSV WITH HEADERS FROM 'file:///relationships/paper_mentions_disease.csv' AS row
MATCH (rp:ResearchPaper {paper_id: row.paper_id})
MATCH (dis:Disease {disease_id: row.disease_id})
CREATE (rp)-[:MENTIONS {mention_count: toInteger(row.mention_count)}]->(dis);

// ResearchPaper -[MENTIONS]-> Drug
LOAD CSV WITH HEADERS FROM 'file:///relationships/paper_mentions_drug.csv' AS row
MATCH (rp:ResearchPaper {paper_id: row.paper_id})
MATCH (d:Drug {drug_id: row.drug_id})
CREATE (rp)-[:MENTIONS {mention_count: toInteger(row.mention_count)}]->(d);

// Researcher -[AFFILIATED_WITH]-> Institution
LOAD CSV WITH HEADERS FROM 'file:///relationships/researcher_affiliated_with.csv' AS row
MATCH (r:Researcher {researcher_id: row.researcher_id})
MATCH (i:Institution {institution_id: row.institution_id})
CREATE (r)-[:AFFILIATED_WITH {start_year: toInteger(row.start_year), role: row.role}]->(i);

// ============================================================
// STEP 4: LOAD NEW RELATIONSHIPS (PATHWAY, ANATOMY, CELLTYPE, BP, MF)
// ============================================================

// Gene -[PARTICIPATES_IN]-> Pathway
LOAD CSV WITH HEADERS FROM 'file:///relationships/gene_participates_in_pathway.csv' AS row
MATCH (g:Gene {gene_id: row.gene_id})
MATCH (pw:Pathway {pathway_id: row.pathway_id})
CREATE (g)-[:PARTICIPATES_IN {role: row.role, evidence: row.evidence}]->(pw);

// Protein -[INVOLVED_IN]-> Pathway
LOAD CSV WITH HEADERS FROM 'file:///relationships/protein_involved_in_pathway.csv' AS row
MATCH (p:Protein {protein_id: row.protein_id})
MATCH (pw:Pathway {pathway_id: row.pathway_id})
CREATE (p)-[:INVOLVED_IN {role: row.role, interaction_type: row.interaction_type}]->(pw);

// Pathway -[REGULATES]-> BiologicalProcess
LOAD CSV WITH HEADERS FROM 'file:///relationships/pathway_involves_biological_process.csv' AS row
MATCH (pw:Pathway {pathway_id: row.pathway_id})
MATCH (bp:BiologicalProcess {process_id: row.process_id})
CREATE (pw)-[:REGULATES {relationship: row.relationship, description: row.description}]->(bp);

// Gene -[INVOLVED_IN]-> BiologicalProcess
LOAD CSV WITH HEADERS FROM 'file:///relationships/gene_involved_in_biological_process.csv' AS row
MATCH (g:Gene {gene_id: row.gene_id})
MATCH (bp:BiologicalProcess {process_id: row.process_id})
CREATE (g)-[:INVOLVED_IN {evidence_code: row.evidence_code, qualifier: row.qualifier}]->(bp);

// Protein -[INVOLVED_IN]-> BiologicalProcess
LOAD CSV WITH HEADERS FROM 'file:///relationships/protein_involved_in_biological_process.csv' AS row
MATCH (p:Protein {protein_id: row.protein_id})
MATCH (bp:BiologicalProcess {process_id: row.process_id})
CREATE (p)-[:INVOLVED_IN {evidence_code: row.evidence_code, qualifier: row.qualifier}]->(bp);

// Gene -[HAS_FUNCTION]-> MolecularFunction
LOAD CSV WITH HEADERS FROM 'file:///relationships/gene_has_molecular_function.csv' AS row
MATCH (g:Gene {gene_id: row.gene_id})
MATCH (mf:MolecularFunction {function_id: row.function_id})
CREATE (g)-[:HAS_FUNCTION {evidence_code: row.evidence_code, qualifier: row.qualifier}]->(mf);

// Protein -[HAS_FUNCTION]-> MolecularFunction
LOAD CSV WITH HEADERS FROM 'file:///relationships/protein_has_molecular_function.csv' AS row
MATCH (p:Protein {protein_id: row.protein_id})
MATCH (mf:MolecularFunction {function_id: row.function_id})
CREATE (p)-[:HAS_FUNCTION {evidence_code: row.evidence_code, qualifier: row.qualifier}]->(mf);

// Protein -[EXPRESSED_IN]-> Anatomy
LOAD CSV WITH HEADERS FROM 'file:///relationships/protein_expressed_in_anatomy.csv' AS row
MATCH (p:Protein {protein_id: row.protein_id})
MATCH (an:Anatomy {anatomy_id: row.anatomy_id})
CREATE (p)-[:EXPRESSED_IN {expression_level: row.expression_level, evidence: row.evidence}]->(an);

// Disease -[AFFECTS]-> Anatomy
LOAD CSV WITH HEADERS FROM 'file:///relationships/disease_affects_anatomy.csv' AS row
MATCH (dis:Disease {disease_id: row.disease_id})
MATCH (an:Anatomy {anatomy_id: row.anatomy_id})
CREATE (dis)-[:AFFECTS {primary_site: row.primary_site, severity: row.severity}]->(an);

// CellType -[FOUND_IN]-> Anatomy
LOAD CSV WITH HEADERS FROM 'file:///relationships/cell_type_found_in_anatomy.csv' AS row
MATCH (ctype:CellType {cell_type_id: row.cell_type_id})
MATCH (an:Anatomy {anatomy_id: row.anatomy_id})
CREATE (ctype)-[:FOUND_IN {abundance: row.abundance, state: row.state}]->(an);

// Disease -[INVOLVES]-> CellType
LOAD CSV WITH HEADERS FROM 'file:///relationships/disease_involves_cell_type.csv' AS row
MATCH (dis:Disease {disease_id: row.disease_id})
MATCH (ctype:CellType {cell_type_id: row.cell_type_id})
CREATE (dis)-[:INVOLVES {involvement_type: row.involvement_type, mechanism: row.mechanism}]->(ctype);

// ============================================================
// STEP 5: LOAD NEW RELATIONSHIPS (ENTITY, EXPOSURE, PHENOTYPE, CLUSTER)
// ============================================================

// Cluster -[HAS_SUMMARY]-> ClusterSummary
LOAD CSV WITH HEADERS FROM 'file:///relationships/cluster_has_summary.csv' AS row
MATCH (clu:Cluster {cluster_id: row.cluster_id})
MATCH (cs:ClusterSummary {summary_id: row.summary_id})
CREATE (clu)-[:HAS_SUMMARY {generated_date: row.generated_date, model_version: row.model_version}]->(cs);

// Disease -[HAS_PHENOTYPE]-> Phenotype
LOAD CSV WITH HEADERS FROM 'file:///relationships/disease_has_phenotype.csv' AS row
MATCH (dis:Disease {disease_id: row.disease_id})
MATCH (phe:Phenotype {phenotype_id: row.phenotype_id})
CREATE (dis)-[:HAS_PHENOTYPE {frequency: toFloat(row.frequency), onset: row.onset, severity: row.severity}]->(phe);

// Exposure -[INCREASES_RISK]-> Disease
LOAD CSV WITH HEADERS FROM 'file:///relationships/exposure_increases_risk_disease.csv' AS row
MATCH (exp:Exposure {exposure_id: row.exposure_id})
MATCH (dis:Disease {disease_id: row.disease_id})
CREATE (exp)-[:INCREASES_RISK {relative_risk: toFloat(row.relative_risk), evidence_level: row.evidence_level, mechanism: row.mechanism}]->(dis);

// Exposure -[AFFECTS]-> Gene
LOAD CSV WITH HEADERS FROM 'file:///relationships/exposure_affects_gene.csv' AS row
MATCH (exp:Exposure {exposure_id: row.exposure_id})
MATCH (g:Gene {gene_id: row.gene_id})
CREATE (exp)-[:AFFECTS {effect_type: row.effect_type, mechanism: row.mechanism, evidence_level: row.evidence_level}]->(g);

// Entity -[ASSOCIATED_WITH]-> Disease
LOAD CSV WITH HEADERS FROM 'file:///relationships/entity_associated_with_disease.csv' AS row
MATCH (ent:Entity {entity_id: row.entity_id})
MATCH (dis:Disease {disease_id: row.disease_id})
CREATE (ent)-[:ASSOCIATED_WITH {association_type: row.association_type, evidence: row.evidence, description: row.description}]->(dis);

// Phenotype -[ASSOCIATED_WITH]-> Gene
LOAD CSV WITH HEADERS FROM 'file:///relationships/phenotype_associated_with_gene.csv' AS row
MATCH (phe:Phenotype {phenotype_id: row.phenotype_id})
MATCH (g:Gene {gene_id: row.gene_id})
CREATE (phe)-[:ASSOCIATED_WITH {association_type: row.association_type, evidence_level: row.evidence_level}]->(g);

// Node -[BELONGS_TO]-> Cluster (generic membership)
LOAD CSV WITH HEADERS FROM 'file:///relationships/node_belongs_to_cluster.csv' AS row
WITH row
WHERE row.node_type = 'Drug'
MATCH (d:Drug {drug_id: row.node_id})
MATCH (clu:Cluster {cluster_id: row.cluster_id})
CREATE (d)-[:BELONGS_TO {membership_score: toFloat(row.membership_score)}]->(clu);

LOAD CSV WITH HEADERS FROM 'file:///relationships/node_belongs_to_cluster.csv' AS row
WITH row
WHERE row.node_type = 'Disease'
MATCH (dis:Disease {disease_id: row.node_id})
MATCH (clu:Cluster {cluster_id: row.cluster_id})
CREATE (dis)-[:BELONGS_TO {membership_score: toFloat(row.membership_score)}]->(clu);

// ============================================================
// STEP 5: VERIFY THE GRAPH
// ============================================================

// View schema visualization (produces the graph like the image)
CALL db.schema.visualization();

// Count all nodes
MATCH (n) RETURN labels(n)[0] AS NodeType, count(n) AS Count ORDER BY Count DESC;

// Count all relationships
MATCH ()-[r]->() RETURN type(r) AS RelType, count(r) AS Count ORDER BY Count DESC;

// Total graph stats
MATCH (n) RETURN 'Nodes' AS metric, count(n) AS total
UNION ALL
MATCH ()-[r]->() RETURN 'Relationships' AS metric, count(r) AS total;
