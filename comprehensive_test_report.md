# Comprehensive Test Failures Report

This breakdown covers all test failures and errors found during the full suite run.

## Summary
- **Total Test Files with Failures:** 27
- **Total Test Files with Errors:** 7

## Detailed Breakdown by File

### tests/api/test_payment_stripe_integration.py

**Failures:**
- test_create_subscription_missing_price_id_raises_integration_error: Detailed reason not shown in summary

### tests/api/test_security_governance.py

**Failures:**
- test_summon_disabled_raises: Detailed reason not shown in summary

### tests/api/test_streaming_security.py

**Failures:**
- test_secure_streaming_authentication: Detailed reason not shown in summary
- test_secure_streaming_circuit_breaker: Detailed reason not shown in summary

### tests/api/test_stripe_connect_demo.py

**Failures:**
- test_create_connected_account_is_idempotent_per_user: Detailed reason not shown in summary
- test_thin_requirements_update_persists_meta_and_event: Detailed reason not shown in summary
- test_events_endpoint_returns_most_recent_first: Detailed reason not shown in summary
- test_create_account_route_then_dashboard_shows_connected_account: Detailed reason not shown in summary

### tests/application/resonance/test_databricks_bridge.py

**Failures:**
- test_event_prioritization: Detailed reason not shown in summary
- test_log_event_queuing: Detailed reason not shown in summary
- test_tuning_inbox: Detailed reason not shown in summary

### tests/e2e/test_trust_pipeline.py

**Failures:**
- test_list_models: Detailed reason not shown in summary
- test_privacy_levels: Detailed reason not shown in summary
- test_privacy_stats: Detailed reason not shown in summary
- test_c3_db_orphan_detects_excess_pool: Detailed reason not shown in summary
- test_detector_chain_runs_in_order: Detailed reason not shown in summary

### tests/integration/test_agentic_skills_integration.py

**Failures:**
- test_skills_registry_discovers_skills: Detailed reason not shown in summary
- test_get_skill_metadata: Detailed reason not shown in summary

### tests/integration/test_api_endpoints_comprehensive.py

**Failures:**
- test_security_health_check: Detailed reason not shown in summary

### tests/integration/test_api_simplified.py

**Failures:**
- test_payment_endpoint_validation: Detailed reason not shown in summary
- test_special_characters_handling: Detailed reason not shown in summary

### tests/integration/test_navigation_intelligence.py

**Failures:**
- test_profile_persistence: Detailed reason not shown in summary
- test_task_pattern_tracking: Detailed reason not shown in summary
- test_file_access_patterns: Detailed reason not shown in summary
- test_tool_usage_patterns: Detailed reason not shown in summary
- test_work_pattern_analysis: Detailed reason not shown in summary
- test_decision_matrix_generation: Detailed reason not shown in summary
- test_adaptive_scoring: Detailed reason not shown in summary
- test_path_selection_optimization: Detailed reason not shown in summary

**Errors:**
- test_context_aware_navigation: Setup/Teardown error or missing dependency
- test_learning_feedback_loop: Setup/Teardown error or missing dependency

### tests/integration/test_rag_evolution.py

**Failures:**
- test_sequence_generation: Detailed reason not shown in summary
- test_state_evolution: Detailed reason not shown in summary
- test_state_persistence: Detailed reason not shown in summary
- test_adaptation_feedback: Detailed reason not shown in summary
- test_landscape_capture: Detailed reason not shown in summary
- test_shift_detection: Detailed reason not shown in summary
- test_analysis_integration: Detailed reason not shown in summary
- test_weight_adaptation: Detailed reason not shown in summary
- test_network_adaptation: Detailed reason not shown in summary
- test_adaptation_state_management: Detailed reason not shown in summary

**Errors:**
- test_version_increment: Setup/Teardown error or missing dependency
- test_version_rollback: Setup/Teardown error or missing dependency
- test_state_compatibility: Setup/Teardown error or missing dependency

### tests/integration/test_repositories.py

**Failures:**
- test_cross_repository_transaction: Detailed reason not shown in summary
- test_transaction_rollback_all_repositories: Detailed reason not shown in summary

**Errors:**
- test_create_case: Setup/Teardown error or missing dependency
- test_get_case_by_id: Setup/Teardown error or missing dependency
- test_update_case_status: Setup/Teardown error or missing dependency
- test_get_cases_by_user: Setup/Teardown error or missing dependency
- test_create_api_key: Setup/Teardown error or missing dependency
- test_validate_api_key: Setup/Teardown error or missing dependency
- test_revoke_api_key: Setup/Teardown error or missing dependency
- test_log_api_usage: Setup/Teardown error or missing dependency
- test_get_usage_by_user: Setup/Teardown error or missing dependency
- test_get_usage_statistics: Setup/Teardown error or missing dependency
- test_create_payment: Setup/Teardown error or missing dependency
- test_update_payment_status: Setup/Teardown error or missing dependency
- test_get_payment_by_id: Setup/Teardown error or missing dependency
- test_get_payments_by_user: Setup/Teardown error or missing dependency
- test_transaction_commit: Setup/Teardown error or missing dependency
- test_transaction_rollback: Setup/Teardown error or missing dependency
- test_health_check: Setup/Teardown error or missing dependency

### tests/integration/test_repository_patterns.py

**Failures:**
- test_get_entity_by_id: Detailed reason not shown in summary
- test_update_entity: Detailed reason not shown in summary
- test_delete_entity: Detailed reason not shown in summary
- test_transaction_commit: Detailed reason not shown in summary
- test_transaction_rollback: Detailed reason not shown in summary
- test_atomic_operations: Detailed reason not shown in summary
- test_filter_by_criteria: Detailed reason not shown in summary
- test_order_by_field: Detailed reason not shown in summary
- test_paginate_results: Detailed reason not shown in summary
- test_bulk_operations: Detailed reason not shown in summary
- test_query_optimization: Detailed reason not shown in summary
- test_connection_pooling: Detailed reason not shown in summary

### tests/integration/test_xai_integration.py

**Failures:**
- test_stream_progress_tracking: Detailed reason not shown in summary
- test_stream_processing: Detailed reason not shown in summary
- test_worker_execution: Detailed reason not shown in summary
- test_memory_limits: Detailed reason not shown in summary
- test_server_management: Detailed reason not shown in summary
- test_server_selection: Detailed reason not shown in summary
- test_load_balancing_metrics: Detailed reason not shown in summary
- test_load_adaptation: Detailed reason not shown in summary
- test_end_to_end_workflow: Detailed reason not shown in summary

### tests/integration/tools/test_interfaces_integration.py

**Errors:**
- test_sqlite_schema: Setup/Teardown error or missing dependency
- test_metrics_insertion: Setup/Teardown error or missing dependency
- test_dashboard_collector: Setup/Teardown error or missing dependency

### tests/performance/test_performance_improvements.py

**Failures:**
- test_fallback_mechanism: Detailed reason not shown in summary
- test_conversation_flow: Detailed reason not shown in summary
- test_auto_indexing: Detailed reason not shown in summary

### tests/scratch/test_nomic_v2.py

**Errors:**
- test_nomic_v2_limit: Setup/Teardown error or missing dependency

### tests/scratch/test_rag_precision.py

**Failures:**
- test_precision: RuntimeError: Ol...

### tests/security/test_revocation_integration.py

**Failures:**
- test_verify_jwt_token_with_revocation: Detailed reason not shown in summary

### tests/test_adsr_arena_integration.py

**Failures:**
- test_bridge_release_phase_no_ops: Detailed reason not shown in summary

### tests/test_agentic_api.py

**Errors:**
- test_get_case: AttributeError: 'MockTelemet...
- test_get_reference_file: AttributeError: 'M...

### tests/test_conversational_rag.py

**Failures:**
- test_session_cleanup: Detailed reason not shown in summary
- test_create_conversational_engine: Detailed reason not shown in summary
- test_multi_hop_chain: Detailed reason not shown in summary
- test_chunk_text_function: Detailed reason not shown in summary

**Errors:**
- test_query_with_session: Setup/Teardown error or missing dependency
- test_session_creation: Setup/Teardown error or missing dependency
- test_conversation_stats: Setup/Teardown error or missing dependency
- test_enhance_query_with_context: Setup/Teardown error or missing dependency
- test_improve_citation_quality: Setup/Teardown error or missing dependency
- test_format_citation: Setup/Teardown error or missing dependency

### tests/test_ollama.py

**Failures:**
- test_ollama_tags: httpx.ConnectErro...

### tests/test_parasitical_fixes.py

**Failures:**
- test_engine_dispose_closes_pool: Detailed reason not shown in summary
- test_fastapi_lifespan_dispose: Detailed reason not shown in summary
- test_exact_context_popped: Detailed reason not shown in summary
- test_stack_integrity_verified: Detailed reason not shown in summary

### tests/test_sustain_decay_arena.py

**Failures:**
- test_adsr_attack_maps_to_reward_escalation: Detailed reason not shown in summary
- test_rewarded_entries_sustain_longer: Detailed reason not shown in summary
- test_penalized_entries_decay_faster: Detailed reason not shown in summary

### tests/unified_fabric/test_event_bus_safety.py

**Failures:**
- test_event_creation: Detailed reason not shown in summary
- test_medical_risk_detected: Detailed reason not shown in summary

### tests/unit/test_critical_paths.py

**Failures:**
- test_event_publish_subscribe: Detailed reason not shown in summary

### tests/unit/test_inference_router.py

**Failures:**
- test_list_models_returns_list: Detailed reason not shown in summary
- test_list_models_has_default: Detailed reason not shown in summary

### tests/unit/test_privacy_router.py

**Failures:**
- test_levels_returns_all_three: Detailed reason not shown in summary
- test_default_level_is_balanced: Detailed reason not shown in summary
- test_stats_returns_counters: Detailed reason not shown in summary

### tests/unit/test_skills_discovery_sandbox.py

**Failures:**
- test_capture_and_list_versions: Detailed reason not shown in summary
- test_rollback_restores_content: Detailed reason not shown in summary

