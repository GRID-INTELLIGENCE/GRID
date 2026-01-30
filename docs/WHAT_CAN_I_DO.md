# What can I do with GRID (Skills + RAG)

This page is a practical menu of high-signal things to run.

## 1) Turn messy text into structured frameworks

### A) Context Engineering (CES/TCoS)

```powershell
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'Context Engineering Service: vector-based indexing, semantic recall, contradiction resolution. Retrieval logic: Primary Recall, Contextual Recall, Contradiction Flagging. Next: integrate thought_signature with StepBloom IF-THEN.', target_schema:'context_engineering', output_format:'json', use_llm:false}"
```

### B) Resonance

```powershell
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'The Resonance Framework: 1) Identify core challenges. 2) Break challenges into manageable components. 3) Balance structure and flexibility. Mystique Activation: Purpose: add mentorship. How it works: user selects character. Examples: What would Uncle Iroh say?', target_schema:'resonance', output_format:'json', use_llm:false}"
```

### C) Knowledgebase (Shield/Sword)

```powershell
.\venv\Scripts\python.exe -m grid skills run transform.schema_map --args-json "{text:'Shield = vetted safe core. Sword = consequences/access control. Define scope rings + timeframes. Add feedback loops and early alerts.', target_schema:'knowledgebase', output_format:'markdown', use_llm:false}"
```

## 2) Reduce noise (collaboration-oriented text cleanup)

### Context refine (heuristic, pronoun-minimizing)

```powershell
.\venv\Scripts\python.exe -m grid skills run context.refine --args-json "{text:'I think we should do it because it is important and it will help us. It will also reduce confusion.', use_llm:false}"
```

## 3) Compress a concept into a strict character budget

```powershell
.\venv\Scripts\python.exe -m grid skills run compress.articulate --args-json "{text:'StepBloom validates steps before proceeding; use IF-THEN checkpoints.', max_chars:80, use_llm:false}"
```

## 4) Explain a concept across domains (map + compass)

```powershell
.\venv\Scripts\python.exe -m grid skills run cross_reference.explain --args-json "{concept:'StepBloom', source_domain:'execution frameworks', target_domain:'software delivery', use_llm:false}"
```

## 5) Analyze a transcript (YouTube-style) locally

```powershell
.\venv\Scripts\python.exe -m grid skills run youtube.transcript_analyze --args-json "{transcript:'[00:00] StepBloom activates a structured execution model. [00:10] IF-THEN checkpoints validate progress.', use_rag:false, top_n:5}"
```

## 6) Build and query the RAG knowledge base (local-first)

### Curated rebuild (recommended)

```powershell
.\venv\Scripts\python.exe -m tools.rag.cli index . --rebuild --curate
```

### Query

```powershell
.\venv\Scripts\python.exe -m tools.rag.cli query "Where is the skills registry implemented?"
```

## 7) Simple manual chaining (copy/paste)

- Run `context.refine` on raw notes
- Feed the refined output into `transform.schema_map` (choose a target schema)
- Optionally compress with `compress.articulate`
