# UI-First Glimpse Artifact Contract + Blueprint Schema
## Reference-Only Foundation Artifact

## 1. Intent

This document is a **reference schema** for design, review, and construction planning.

It combines three layers:

- **Layer A — Trust contract**
  - derived from `TUV-001 v1.0.0`
- **Layer B — Runtime contract**
  - derived from the implemented `glimpse-artifact` request/response flow
- **Layer C — Mechanical pencil sketch blueprint**
  - a UI/UX layout reference that describes zones, seams, controls, and display surfaces

This document does **not** amend TUV-001.
It derives from it.

## 2. Authority Order

Use this order when reading or building from this schema:

1. **Authoritative contract source**
   - `/home/caraxes/seed/templates/development-contract.md`
2. **Implemented runtime**
   - `glimpse-artifact/server/context-search.ts`
   - `glimpse-artifact/server/vite-api-plugin.ts`
   - `glimpse-artifact/src/views/ContextSearchView.tsx`
   - `glimpse-artifact/src/hooks/useContextSearch.ts`
   - `glimpse-artifact/src/components/phase4/types.ts`
3. **Adjacent UI surface**
   - `glimpse-artifact/src/views/ScenarioCanvasView.tsx`
   - `glimpse-artifact/src/hooks/useCanvasSeeds.ts`
4. **Prototype mirror**
   - `GRID/mcp-setup/server/Design a UI-first glimpse-artifact tool `
5. **This document**
   - reference and interpretation only

## 3. Contract Envelope Schema

```yaml
contract_envelope:
  schema_id: ui_first_glimpse_artifact_contract_envelope
  schema_version: 0.1.0
  purpose: reference_only
  source_contract:
    id: TUV-001
    version: 1.0.0
    title: The Unbreakable Vow — Development Contract
    source_path: /home/caraxes/seed/templates/development-contract.md
  activation:
    trigger:
      - developer invokes TUV-001 by name
      - developer uses /activate-tuv
    assistant_acknowledgment_required: true
    session_scope: active_until_explicitly_deactivated
  parties:
    - developer
    - assistant
  conditions:
    fidelity:
      intent: watch over the work
      clauses:
        - id: I.1
          name: provenance_traceability
          effect_on_system:
            - every major output traces to a stated objective
            - no orphaned recommendation or artifact
        - id: I.2
          name: context_awareness
          effect_on_system:
            - context pressure must be surfaced
            - stale or compressed context must be disclosed
        - id: I.3
          name: scope_fidelity
          effect_on_system:
            - scope expansion is flagged before proceeding
            - reference schema must distinguish implemented vs planned paths
    integrity:
      intent: protect the work from harm
      clauses:
        - id: II.1
          name: fail_closed_on_ambiguity
          effect_on_system:
            - unclear requests require clarification
            - no silent guessing in architecture interpretation
        - id: II.2
          name: anti_degradation_signal
          effect_on_system:
            - declining certainty must be stated
            - reference diagrams cannot pretend to be runtime truth
        - id: II.3
          name: periodic_realignment
          effect_on_system:
            - architecture summaries must restate current understanding at breakpoints
    accountability:
      intent: carry the failure if it fails
      clauses:
        - id: III.1
          name: self_reporting
          effect_on_system:
            - mistaken architecture claims must be corrected explicitly
        - id: III.2
          name: human_override_authority
          effect_on_system:
            - the developer can redirect format, structure, or emphasis
        - id: III.3
          name: immutable_versioning
          effect_on_system:
            - source contract is not silently modified by this reference artifact
  never_rules:
    - id: NR-01
      rule: never_silently_discard_context
    - id: NR-02
      rule: never_present_known_incorrect_output_as_certain
    - id: NR-03
      rule: never_resist_or_delay_human_override
    - id: NR-04
      rule: never_amend_the_contract_unilaterally
    - id: NR-05
      rule: never_conceal_a_known_violation
  violation_protocols:
    condition_i: output_void_and_reanchor
    condition_ii: shield_break
    condition_iii: breach_state
  design_implications:
    - evidence must stay visible in the interface
    - unknown terms must remain visible rather than silently absorbed
    - provider selection must not become truth authority without grounded checks
    - reference documentation must separate implemented runtime from adjacent ideas
```

## 4. Runtime Contract Schema

```yaml
runtime_contract:
  schema_id: ui_first_glimpse_artifact_runtime_contract
  schema_version: 0.1.0
  request:
    type_name: ContextSearchRequest
    transport: POST
    primary_endpoint: /api/context-search/interview
    sibling_endpoints:
      - /api/context-search/keywords
      - /api/context-search/query
    fields:
      scenarioText:
        type: string
        required: true
        rule: trimmed_value_must_be_non_empty
      optionalContext:
        type: string
        required: false
      optionalProblemFrame:
        type: string
        required: false
      maxKeywords:
        type: integer
        required: false
        default: 8
        clamp: [5, 12]
      provider:
        type: enum
        required: false
        allowed:
          - deterministic
          - openai
          - ollama
        current_ui_state:
          deterministic: enabled
          openai: disabled
          ollama: disabled
  orchestration:
    entrypoint: runContextSearch
    ordered_steps:
      - validate_scenario_text
      - get_or_build_repo_index
      - build_keyword_bundle
      - search_indexed_documents
      - build_graph
      - build_clusters
      - build_heatmap
      - build_summary
      - build_interview_script
      - package_context_search_result
  response:
    type_name: ContextSearchResult
    sections:
      keywords:
        accepted:
          item_fields:
            - term
            - canonicalTerm
            - weight
            - expansions
            - source
        rejectedTerms: string[]
        unknownTerms: string[]
        synthesisTrace: string[]
      summary: string
      hits:
        item_fields:
          - id
          - path
          - title
          - cluster
          - kind
          - score
          - matchedTerms
          - symbolMatches
          - exactPathMatches
          - contentMatches
          - excerpt
      graph:
        nodes:
          item_fields:
            - id
            - label
            - type
            - cluster
            - score
        edges:
          item_fields:
            - source
            - target
            - type
            - weight
            - label
      clusters:
        item_fields:
          - id
          - label
          - score
          - matchedTerms
          - topHitIds
          - transferReasons
      heatmap:
        item_fields:
          - keyword
          - clusterId
          - score
      artifacts:
        item_fields:
          - id
          - type
          - title
          - content
          - evidenceRefs
      interview:
        speakers:
          item_fields:
            - id
            - label
            - role
        turns:
          item_fields:
            - id
            - speakerId
            - text
            - evidenceRefs
            - artifactRefs
            - confidence
  scoring_preferences:
    path_token_match: 3.2
    symbol_token_match: 2.4
    token_presence: 1.2
    content_occurrence: 0.55
    content_occurrence_cap_per_term: 4
    kind_weights:
      view: 1.18
      hook: 1.18
      component: 1.18
      doc: 0.95
      default: 1.0
  limits:
    returned_hits_max: 18
    returned_clusters_max: 8
    index_cache_ttl_ms: 15000
  search_posture:
    deterministic_first: true
    evidence_grounded: true
    exportable_result_package: true
    provider_is_hint_not_truth_authority: true
```

## 5. Blueprint Envelope Schema

```yaml
blueprint_envelope:
  schema_id: ui_first_glimpse_artifact_blueprint
  schema_version: 0.1.0
  drawing_style:
    metaphor: mechanical_engineering_pencil_sketch
    output_use: reference_only
    visual_tone:
      - graphite
      - blueprint_notation
      - callout_labels
      - panel_boundaries
      - measured_sections
  legend:
    solid_outline: implemented_load_bearing_boundary
    dashed_outline: future_or_optional_seam
    hatch_teal: evidence_or_active_analysis_zone
    hatch_amber: cluster_or_transfer_zone
    neutral_fill: structural_container
    numbered_callout: interaction_sequence_reference
  layout_orientation:
    reading_order: top_to_bottom
    dependency_view: vertical
    emphasis_view: sectional
```

## 6. Mechanical Pencil Sketch — Front Elevation

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ A. HEADER RAIL                                                              │
│ title / mode marker / framing sentence                                      │
│ run state / export trigger / session identity                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ B. INPUT BENCH                                                              │
│ scenario text                                                               │
│ optional context                                                            │
│ optional problem frame                                                      │
│ max keywords / provider / reset / analyze                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ C. KEYWORD AND TRACE DECK                                                   │
│ accepted keywords / unknown terms / synthesis trace / summary               │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ D1. VISIBILITY CHAMBER        │ D2. CLUSTER RANKING COLUMN                  │
│ graph nodes and edges         │ ranked clusters                             │
│ file-to-cluster belongs_to    │ matched terms                               │
│ file-to-file references       │ transfer reasons                            │
│ cluster-to-cluster transfer   │ score concentration                         │
├───────────────────────────────┴──────────────────────────────────────────────┤
│ E. HEATMAP PLATE                                                        [E] │
│ keyword x cluster score distribution                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│ F. INTERVIEW BAY                                                        [F] │
│ interviewer / retriever / mapper / skeptic / synthesizer                    │
│ evidence refs / artifact refs / confidence                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ G. ARTIFACT TRAY                                                        [G] │
│ paragraph / graph / cluster map / heatmap / checklist                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ H. EVIDENCE RACK                                                        [H] │
│ path / title / kind / score / excerpt / matched terms                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 7. Mechanical Pencil Sketch — Section A-A (Runtime Cut)

```text
[User Input]
    │
    ▼
[ContextSearchView]
    │ form submit
    ▼
[useContextSearch]
    │ fetch POST /api/context-search/interview
    ▼
[Vite API boundary]
    │ runContextSearch(body, CASCADE_ROOT)
    ▼
[Orchestration Spine]
    ├─ buildIndex / getIndexedRepo
    ├─ buildKeywordBundleFromText
    ├─ searchIndexedDocuments
    ├─ buildGraph
    ├─ buildClusters
    ├─ buildHeatmap
    ├─ buildSummary
    └─ buildInterviewScript
    │
    ▼
[ContextSearchResult]
    │
    ▼
[Rendered UI Sections]
```

## 8. Panel-by-Panel UI/UX Schema

```yaml
ui_panels:
  header_rail:
    purpose: orient_the_user_and_hold_global_controls
    actual_signals:
      - title
      - short framing sentence
    construction_notes:
      - should remain thin and stable
      - should not carry detailed evidence
  input_bench:
    purpose: gather_problem_framing_before_search
    controls:
      - scenario_text
      - optional_context
      - optional_problem_frame
      - max_keywords
      - provider
      - reset
      - analyze_context
    construction_notes:
      - this is the highest leverage input surface
      - ambiguity should be resolved here rather than downstream
  keyword_trace_deck:
    purpose: expose_compression_output_before_deep_interpretation
    displays:
      - accepted_keywords
      - unknown_terms
      - synthesis_trace
      - summary
    construction_notes:
      - makes the search legible
      - keeps compression auditable
  visibility_chamber:
    purpose: show_node_and_cluster_topology
    displays:
      - graph_nodes
      - graph_edges
      - transfer_edges
    construction_notes:
      - cluster edges are relationship cues, not truth by themselves
      - this panel explains structure, not final judgment
  cluster_ranking_column:
    purpose: rank_concentration_by_subsystem_family
    displays:
      - cluster_score
      - matched_terms
      - transfer_reasons
    construction_notes:
      - this is the quickest scan for where the repo answers from
  heatmap_plate:
    purpose: show_distribution_of_accepted_keywords_across_clusters
    displays:
      - keyword_to_cluster_scores
    construction_notes:
      - best for breadth inspection
      - should remain comparable across runs
  interview_bay:
    purpose: convert_grounded_evidence_into_portable_discussion_form
    displays:
      - speakers
      - turns
      - evidence_refs
      - artifact_refs
      - confidence
    construction_notes:
      - transcript must remain downstream of evidence
      - confidence is framing, not proof
  artifact_tray:
    purpose: package_results_into_transportable_forms
    displays:
      - paragraph
      - graph
      - cluster_map
      - heatmap
      - checklist
    construction_notes:
      - artifacts should remain export-friendly
  evidence_rack:
    purpose: expose_raw_supporting_hits
    displays:
      - title
      - path
      - kind
      - score
      - excerpt
      - matched_terms
    construction_notes:
      - this is the most load-bearing trust surface
      - every higher layer should be explainable from here
```

## 9. State Machine Schema

```yaml
state_machine:
  idle:
    meaning: no_result_yet
    visible_surfaces:
      - input_bench
      - empty_state_prompt
  loading:
    meaning: request_in_flight
    visible_surfaces:
      - input_bench_locked_submit
      - loading_label
  error:
    meaning: request_failed_or_invalid
    visible_surfaces:
      - input_bench
      - error_panel
      - retry_action
  result:
    meaning: grounded_result_available
    visible_surfaces:
      - keyword_trace_deck
      - visibility_chamber
      - cluster_ranking_column
      - heatmap_plate
      - interview_bay
      - artifact_tray
      - evidence_rack
```

## 10. Foundation Flags and Construction Preferences

```yaml
foundation_flags:
  trust_contract_active: true
  deterministic_first: true
  evidence_first: true
  repo_native_search: true
  vector_store_required: false
  provider_expandable: true
  provider_authoritative: false
  export_package_expected: true
  unknown_terms_visible: true
  implemented_runtime_separate_from_prototype: true
  canvas_separate_from_context_search: true

construction_preferences:
  preserve_result_contract_first: true
  preserve_evidence_refs: true
  preserve_unknown_term_visibility: true
  preserve_traceability_from_summary_to_hits: true
  add_new_providers_behind_existing_contract: true
  couple_canvas_only_with_explicit_request_schema: true
  prefer_reference_docs_that_distinguish_actual_vs_planned: true
```

## 11. Construction Notes — What Is Load-Bearing

- **Load-bearing**
  - `scenarioText` validation
  - deterministic keyword bundle formation
  - evidence hit scoring
  - cluster aggregation
  - traceable artifact packaging
  - visible unknown terms
  - exportable typed result

- **Support structure**
  - graph layout
  - section arrangement
  - transcript framing
  - cluster visibility presentation

- **Optional seam**
  - provider-specific model assistance
  - canvas-to-search coupling
  - Python-to-TypeScript schema parity
  - richer blueprint rendering

## 12. Construction Notes — What Must Stay Decoupled Until Explicitly Joined

- the **scenario canvas** should not silently become the context-search driver
- the **Python prototype** should not be assumed to be a production peer without a shared schema
- the **provider enum** should not imply live provider parity
- the **diagram colors** should not be treated as normative runtime truth without a legend contract

## 13. Short Build Sequence

```yaml
recommended_build_sequence:
  - stabilize_request_response_schema
  - preserve_deterministic_scoring_as_reference_path
  - keep_evidence_rack_and_trace_surfaces_visible
  - define_shared_schema_if_python_and_typescript_are_to_converge
  - define_explicit_canvas_to_search_contract_before_integration
  - add_provider_specific_adapters_only_after_grounding_rules_are_preserved
```

## 14. One-Line Reference Summary

This system should be built and read as a **contract-governed, deterministic, evidence-first context-search instrument** with a **mechanical, vertically layered UI** whose higher-level summaries remain explainable from the evidence rack upward.
