# GRID Repository Terrain Map

Generated terrain map of the repository structure, packages, imports, and dependencies.

## Summary

- **Total Packages**: 7
- **Packages with src/ imports**: 16
- **Packages with grid/ imports**: 78
- **Path-sensitive files**: 5
- **Conceptual duplicates**: 1
- **Cache directories found**: 157

## Packages

### application/
- Path: `application`
- Has __init__.py: True
- Submodules: mothership, resonance

### core/
- Path: `core`
- Has __init__.py: True

### grid/
- Path: `grid`
- Has __init__.py: True
- Submodules: awareness, entry_points, essence, evolution, interfaces, organization, patterns, processing, prompts, quantum, rag, senses, skills, tracing

### models/
- Path: `models`
- Has __init__.py: True

### python/
- Path: `python`
- Has __init__.py: True

### tools/
- Path: `tools`
- Has __init__.py: True
- Submodules: rag

### workflows/
- Path: `workflows`
- Has __init__.py: True

## Import Patterns

### From src/ imports
- `application\resonance\api\performance.py:grid`
- `light_of_the_seven\light_of_the_seven\tests\test_sorting.py:light_of_the_seven`
- `src\cli\main.py:services`
- `src\grid\pattern\engine.py:grid`
- `test_retry_limit.py:kernel`
- `tests\integration\test_pipeline_robustness.py:grid`
- `tests\integration\test_pipeline_robustness.py:kernel`
- `tests\unit\test_cli.py:cli`
- `tests\unit\test_contribution_tracker.py:services`
- `tests\unit\test_intelligent_routing.py:kernel`
- `tests\unit\test_message_broker_retry_persistence.py:kernel`
- `tests\unit\test_nl_dev.py:nl_dev`
- `tests\unit\test_pattern_engine_dbscan.py:grid`
- `tests\unit\test_pattern_engine_matching.py:grid`
- `tests\unit\test_pattern_engine_mist.py:grid`
- `tests\unit\test_pattern_engine_rag.py:grid`

### From grid/ imports (canonical)
- `.claude\skills\analysis_process_context.py:skills`
- `.claude\skills\intelligence_git_analyze.py:skills`
- `.claude\skills\patterns_detect_entities.py:skills`
- `.claude\skills\rag_query_knowledge.py:skills`
- `application\mothership\routers\__init__.py:AGENT`
- `application\mothership\routers\intelligence.py:application`
- `application\resonance\api\router.py:skills`
- `application\resonance\api\router.py:tracing`
- `archival\experiments\example_codestral_usage.py:codestral_client`
- `async_stress_harness.py:application`
- `examples\translator_demo.py:services`
- `grid\__main__.py:application`
- `grid\__main__.py:skills`
- `grid\application.py:awareness`
- `grid\application.py:essence`
- `grid\application.py:evolution`
- `grid\application.py:interfaces`
- `grid\application.py:patterns`
- `grid\awareness\context.py:essence`
- `grid\entry_points\api_entry.py:organization`
- ... and 58 more

## Path-Sensitive Files (Must Stay at Root)

- **benchmark_metrics.json**: Referenced in `tests\test_grid_benchmark.py` (Hardcoded in test)
- **benchmark_results.json**: Referenced in `tests\test_grid_benchmark.py` (Hardcoded in test)
- **benchmark_metrics.json**: Referenced in `tests\performance\test_resonance_load.py` (Hardcoded in test)
- **benchmark_results.json**: Referenced in `research_snapshots\light_of_the_seven_repo_copy_2026-01-01\tests\test_grid_benchmark.py` (Hardcoded in test)
- **stress_metrics.json**: Referenced in `async_stress_harness.py` (Default output path)

## Conceptual Duplicates

- **conceptual_duplicate**: src\grid, grid
  - src/grid/ and grid/ both exist (legacy vs canonical)

## Cache Directories (Cleanup Candidates)

Found 157 cache directories:

- `.pytest_cache`
- `.ruff_cache`
- `Hogwarts\hogwarts-visualizer\node_modules`
- `SEGA\__pycache__`
- `__pycache__`
- `acoustics\__pycache__`
- `application\__pycache__`
- `application\mothership\__pycache__`
- `application\mothership\middleware\__pycache__`
- `application\mothership\models\__pycache__`
- `application\mothership\repositories\__pycache__`
- `application\mothership\routers\__pycache__`
- `application\mothership\schemas\__pycache__`
- `application\mothership\security\__pycache__`
- `application\mothership\services\__pycache__`
- `application\mothership\services\billing\__pycache__`
- `application\mothership\services\payment\__pycache__`
- `application\resonance\__pycache__`
- `application\resonance\api\__pycache__`
- `archival\atmosphere\Atmosphere\.pytest_cache`
- `archival\atmosphere\Atmosphere\.ruff_cache`
- `archival\atmosphere\Atmosphere\Delay\.mypy_cache`
- `archival\atmosphere\Atmosphere\Echoes\.artifacts\htmlcov`
- `archival\atmosphere\Atmosphere\Echoes\.mypy_cache`
- `archival\atmosphere\Atmosphere\Echoes\.pytest_cache`
- `archival\atmosphere\Atmosphere\Echoes\.root_backup\20251101_072940_integrations\.ruff_cache`
- `archival\atmosphere\Atmosphere\Echoes\.ruff_cache`
- `archival\atmosphere\Atmosphere\Echoes\echoes_core\security_audit\quarantine\parasitic_removed\misc\integrations\.ruff_cache`
- `archival\atmosphere\Atmosphere\Echoes\misc\integrations\.ruff_cache`
- `archival\atmosphere\Atmosphere\Echoes\root_configs\.ruff_cache`
- `archival\atmosphere\Atmosphere\Reverb\.mypy_cache`
- `archival\atmosphere\Atmosphere\atmosphere_domains\api_client\.pytest_cache`
- `archival\atmosphere\Atmosphere\atmosphere_domains\arcade_optimizer\.pytest_cache`
- `archival\atmosphere\Atmosphere\atmosphere_domains\echoes_mapper\.pytest_cache`
- `archival\atmosphere\Atmosphere\htmlcov`
- `archival\atmosphere\Atmosphere\network-visualizer-python\.pytest_cache`
- `archival\atmosphere\Atmosphere\reference_harmonizer\.pytest_cache`
- `archival\atmosphere\Atmosphere\tests\.pytest_cache`
- `archival\python_unclear\Python\.pytest_cache`
- `archival\python_unclear\Python\.ruff_cache`
- `awareness\__pycache__`
- `backend\Explore\ui\node_modules`
- `backend\Explore\ui\node_modules\@eslint-community\eslint-utils\node_modules`
- `backend\Explore\ui\node_modules\@eslint\eslintrc\node_modules`
- `backend\Explore\ui\node_modules\@react-three\fiber\node_modules`
- `backend\Explore\ui\node_modules\@typescript-eslint\eslint-plugin\node_modules`
- `backend\Explore\ui\node_modules\@typescript-eslint\typescript-estree\node_modules`
- `backend\Explore\ui\node_modules\its-fine\node_modules`
- `backend\Explore\ui\node_modules\react-reconciler\node_modules`
- `backend\Explore\ui\node_modules\rolldown\node_modules`
- ... and 107 more
