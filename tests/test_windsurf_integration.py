"""
Tests for Windsurf feature integration with OVERWATCH.

Validates Arena Mode, Plan Mode, Cascade Hooks, MCP Servers,
and Gemini 3 Flash model integration.
"""

import pytest

from Arena.the_chase.python.src.the_chase.overwatch.arena_mode import OverwatchArenaMode
from Arena.the_chase.python.src.the_chase.overwatch.hooks import OverwatchHooks
from Arena.the_chase.python.src.the_chase.overwatch.mcp import OverwatchMCP
from Arena.the_chase.python.src.the_chase.overwatch.models import OverwatchModels
from Arena.the_chase.python.src.the_chase.overwatch.plan_mode import OverwatchPlanMode


class TestArenaMode:
    """Test suite for Arena Mode integration."""

    @pytest.fixture
    def arena_mode(self) -> OverwatchArenaMode:
        """Create Arena Mode instance."""
        return OverwatchArenaMode()

    def test_arena_mode_initialization(self, arena_mode: OverwatchArenaMode):
        """Verify Arena Mode initializes correctly."""
        assert arena_mode.battle_groups == []
        assert arena_mode.personal_leaderboard == {}
        assert arena_mode.global_leaderboard == {}

    def test_compare_models_returns_dict(self, arena_mode: OverwatchArenaMode):
        """Verify compare_models returns dictionary."""
        results = arena_mode.compare_models("test prompt", ["model1", "model2"])
        assert isinstance(results, dict)
        assert len(results) == 2

    def test_compare_models_single_model(self, arena_mode: OverwatchArenaMode):
        """Verify compare_models with single model."""
        results = arena_mode.compare_models("test prompt", ["gemini_3_flash"])
        assert len(results) == 1
        assert "gemini_3_flash" in results

    def test_compare_models_empty_list(self, arena_mode: OverwatchArenaMode):
        """Verify compare_models with empty model list."""
        results = arena_mode.compare_models("test prompt", [])
        assert results == {}

    def test_execute_with_model_returns_string(self, arena_mode: OverwatchArenaMode):
        """Verify _execute_with_model returns string."""
        result = arena_mode._execute_with_model("test prompt", "model1")
        assert isinstance(result, str)
        assert "model1" in result

    def test_compare_models_preserves_order(self, arena_mode: OverwatchArenaMode):
        """Verify compare_models preserves model order."""
        models = ["model_a", "model_b", "model_c"]
        results = arena_mode.compare_models("test prompt", models)
        assert list(results.keys()) == models

    def test_battle_groups_empty_initially(self, arena_mode: OverwatchArenaMode):
        """Verify battle groups start empty."""
        assert len(arena_mode.battle_groups) == 0

    def test_leaderboards_empty_initially(self, arena_mode: OverwatchArenaMode):
        """Verify leaderboards start empty."""
        assert len(arena_mode.personal_leaderboard) == 0
        assert len(arena_mode.global_leaderboard) == 0


class TestPlanMode:
    """Test suite for Plan Mode integration."""

    @pytest.fixture
    def plan_mode(self) -> OverwatchPlanMode:
        """Create Plan Mode instance."""
        return OverwatchPlanMode()

    def test_plan_mode_initialization(self, plan_mode: OverwatchPlanMode):
        """Verify Plan Mode initializes correctly."""
        assert plan_mode is not None

    def test_create_plan_returns_dict(self, plan_mode: OverwatchPlanMode):
        """Verify create_plan returns dictionary."""
        plan = plan_mode.create_plan("implement feature")
        assert isinstance(plan, dict)

    def test_create_plan_has_required_keys(self, plan_mode: OverwatchPlanMode):
        """Verify plan has all required keys."""
        plan = plan_mode.create_plan("implement feature")
        assert 'steps' in plan
        assert 'dependencies' in plan
        assert 'risks' in plan
        assert 'timeline' in plan

    def test_create_plan_adds_objective_step(self, plan_mode: OverwatchPlanMode):
        """Verify plan includes objective definition."""
        plan = plan_mode.create_plan("test task")
        assert len(plan['steps']) > 0
        assert any("test task" in step for step in plan['steps'])

    def test_create_plan_has_risks(self, plan_mode: OverwatchPlanMode):
        """Verify plan includes risk assessment."""
        plan = plan_mode.create_plan("test task")
        assert len(plan['risks']) > 0

    def test_create_plan_has_timeline(self, plan_mode: OverwatchPlanMode):
        """Verify plan includes timeline estimate."""
        plan = plan_mode.create_plan("test task")
        assert 'estimate' in plan['timeline']

    def test_create_plan_empty_task(self, plan_mode: OverwatchPlanMode):
        """Verify plan creation with empty task."""
        plan = plan_mode.create_plan("")
        assert isinstance(plan, dict)
        assert 'steps' in plan

    def test_create_plan_complex_task(self, plan_mode: OverwatchPlanMode):
        """Verify plan creation with complex task."""
        plan = plan_mode.create_plan("implement distributed system with microservices")
        assert len(plan['steps']) > 0
        assert len(plan['risks']) > 0


class TestCascadeHooks:
    """Test suite for Cascade Hooks integration."""

    @pytest.fixture
    def hooks(self) -> OverwatchHooks:
        """Create Hooks instance."""
        return OverwatchHooks()

    def test_hooks_initialization(self, hooks: OverwatchHooks):
        """Verify hooks initialize with empty lists."""
        assert hooks.hooks['pre_user_prompt'] == []
        assert hooks.hooks['post_cascade_response'] == []

    def test_register_hook_adds_callback(self, hooks: OverwatchHooks):
        """Verify register_hook adds callback to list."""
        def dummy_callback(*args, **kwargs):
            pass

        hooks.register_hook('pre_user_prompt', dummy_callback)
        assert len(hooks.hooks['pre_user_prompt']) == 1

    def test_register_hook_multiple_callbacks(self, hooks: OverwatchHooks):
        """Verify multiple callbacks can be registered."""
        def callback1(*args, **kwargs):
            pass
        def callback2(*args, **kwargs):
            pass

        hooks.register_hook('pre_user_prompt', callback1)
        hooks.register_hook('pre_user_prompt', callback2)
        assert len(hooks.hooks['pre_user_prompt']) == 2

    def test_register_hook_invalid_event(self, hooks: OverwatchHooks):
        """Verify register_hook ignores invalid events."""
        def dummy_callback(*args, **kwargs):
            pass

        hooks.register_hook('invalid_event', dummy_callback)
        # Should not raise, just ignore

    def test_trigger_hook_calls_callbacks(self, hooks: OverwatchHooks):
        """Verify trigger_hook calls all registered callbacks."""
        callback_called = [False]

        def dummy_callback(*args, **kwargs):
            callback_called[0] = True

        hooks.register_hook('pre_user_prompt', dummy_callback)
        hooks.trigger_hook('pre_user_prompt', "test prompt")

        assert callback_called[0] is True

    def test_trigger_hook_with_args(self, hooks: OverwatchHooks):
        """Verify trigger_hook passes arguments to callbacks."""
        received_args = []

        def dummy_callback(*args, **kwargs):
            received_args.append(args)

        hooks.register_hook('post_cascade_response', dummy_callback)
        hooks.trigger_hook('post_cascade_response', "response", 100)

        assert len(received_args) == 1
        assert received_args[0] == ("response", 100)

    def test_trigger_hook_no_callbacks(self, hooks: OverwatchHooks):
        """Verify trigger_hook works with no callbacks registered."""
        # Should not raise
        hooks.trigger_hook('pre_user_prompt', "test")

    def test_trigger_hook_invalid_event(self, hooks: OverwatchHooks):
        """Verify trigger_hook ignores invalid events."""
        # Should not raise
        hooks.trigger_hook('invalid_event')


class TestMCPServers:
    """Test suite for MCP Server integration."""

    @pytest.fixture
    def mcp_config(self) -> dict:
        """Create MCP configuration."""
        return {
            'servers': {
                'grid_rag': {'url': 'http://localhost:8080'},
                'portfolio_safety': {'url': 'http://localhost:8081'},
            }
        }

    @pytest.fixture
    def mcp(self, mcp_config: dict) -> OverwatchMCP:
        """Create MCP instance."""
        return OverwatchMCP(mcp_config)

    def test_mcp_initialization(self, mcp: OverwatchMCP):
        """Verify MCP initializes with server config."""
        assert len(mcp.mcp_servers) > 0

    def test_call_mcp_tool_existing_server(self, mcp: OverwatchMCP):
        """Verify calling tool on existing server."""
        result = mcp.call_mcp_tool('grid_rag', 'search', {'query': 'test'})
        assert isinstance(result, dict)
        assert 'status' in result

    def test_call_mcp_tool_nonexistent_server(self, mcp: OverwatchMCP):
        """Verify calling tool on nonexistent server."""
        result = mcp.call_mcp_tool('nonexistent', 'tool', {})
        assert result['status'] == 'error'

    def test_call_mcp_tool_returns_dict(self, mcp: OverwatchMCP):
        """Verify call_mcp_tool returns dictionary."""
        result = mcp.call_mcp_tool('grid_rag', 'test', {})
        assert isinstance(result, dict)

    def test_call_mcp_tool_with_args(self, mcp: OverwatchMCP):
        """Verify tool call with arguments."""
        result = mcp.call_mcp_tool('grid_rag', 'search', {'query': 'test', 'limit': 10})
        assert result['status'] == 'success'

    def test_mcp_empty_config(self):
        """Verify MCP with empty configuration."""
        mcp = OverwatchMCP({})
        assert mcp.mcp_servers == {}

    def test_mcp_config_without_servers(self):
        """Verify MCP config without servers key."""
        mcp = OverwatchMCP({'other_key': 'value'})
        assert mcp.mcp_servers == {}


class TestGemini3Flash:
    """Test suite for Gemini 3 Flash model integration."""

    def test_models_dict_exists(self):
        """Verify OverwatchModels has MODELS dict."""
        assert hasattr(OverwatchModels, 'MODELS')
        assert isinstance(OverwatchModels.MODELS, dict)

    def test_gemini_3_flash_in_models(self):
        """Verify gemini_3_flash is registered."""
        assert 'gemini_3_flash' in OverwatchModels.MODELS

    def test_gemini_3_flash_capabilities(self):
        """Verify gemini_3_flash has correct capabilities."""
        model = OverwatchModels.MODELS['gemini_3_flash']
        assert 'reasoning' in model['capabilities']
        assert 'speed' in model['capabilities']

    def test_gemini_3_flash_use_case(self):
        """Verify gemini_3_flash has correct use case."""
        model = OverwatchModels.MODELS['gemini_3_flash']
        assert model['use_case'] == 'agentic_workflows'


class TestWindsurfIntegrationWorkflows:
    """Workflow tests for Windsurf feature integration."""

    def test_arena_mode_with_plan_mode(self):
        """Test Arena Mode combined with Plan Mode."""
        arena = OverwatchArenaMode()
        plan = OverwatchPlanMode()

        # Create plan for model comparison
        comparison_plan = plan.create_plan("compare models for task")

        # Run comparison
        results = arena.compare_models("test prompt", ["model1", "model2"])

        assert 'steps' in comparison_plan
        assert len(results) == 2

    def test_hooks_with_mcp(self):
        """Test Hooks combined with MCP."""
        hooks = OverwatchHooks()
        mcp = OverwatchMCP({'servers': {'test': {}}})

        # Register hook that calls MCP
        def mcp_hook(server, tool, args):
            return mcp.call_mcp_tool(server, tool, args)

        hooks.register_hook('pre_user_prompt', mcp_hook)
        # Trigger the hook - it returns None because trigger_hook doesn't return values
        hooks.trigger_hook('pre_user_prompt', 'test_server', 'test_tool', {})
        # Test passed if no exception was raised

    def test_full_windsurf_stack(self):
        """Test complete Windsurf feature stack."""
        arena = OverwatchArenaMode()
        plan = OverwatchPlanMode()
        hooks = OverwatchHooks()
        mcp = OverwatchMCP({'servers': {'test': {}}})

        # All should initialize without error
        assert arena is not None
        assert plan is not None
        assert hooks is not None
        assert mcp is not None

        # Verify models are available
        assert 'gemini_3_flash' in OverwatchModels.MODELS

    def test_model_comparison_with_gemini_flash(self):
        """Test model comparison using Gemini 3 Flash."""
        arena = OverwatchArenaMode()
        models = ['gemini_3_flash', 'model_backup']
        results = arena.compare_models("analyze this request", models)

        assert len(results) == 2
        assert 'gemini_3_flash' in results


class TestWindsurfEdgeCases:
    """Edge case tests for Windsurf integration."""

    @pytest.fixture
    def arena_mode(self) -> OverwatchArenaMode:
        """Create Arena Mode instance."""
        return OverwatchArenaMode()

    @pytest.fixture
    def plan_mode(self) -> OverwatchPlanMode:
        """Create Plan Mode instance."""
        return OverwatchPlanMode()

    @pytest.fixture
    def hooks(self) -> OverwatchHooks:
        """Create Hooks instance."""
        return OverwatchHooks()

    @pytest.fixture
    def mcp(self) -> OverwatchMCP:
        """Create MCP instance."""
        return OverwatchMCP({'servers': {'grid_rag': {}}})

    def test_arena_mode_unicode_prompt(self, arena_mode: OverwatchArenaMode):
        """Verify Arena Mode handles unicode prompts."""
        results = arena_mode.compare_models("Hello 世界 🌍", ["model1"])
        assert len(results) == 1

    def test_plan_mode_unicode_task(self, plan_mode: OverwatchPlanMode):
        """Verify Plan Mode handles unicode tasks."""
        plan = plan_mode.create_plan("实现功能")
        assert 'steps' in plan

    def test_hooks_empty_callback(self, hooks: OverwatchHooks):
        """Verify hooks handle empty callback gracefully."""
        def empty_callback():
            pass

        hooks.register_hook('pre_user_prompt', empty_callback)
        hooks.trigger_hook('pre_user_prompt')

    def test_mcp_empty_args(self, mcp: OverwatchMCP):
        """Verify MCP handles empty arguments."""
        result = mcp.call_mcp_tool('grid_rag', 'test', {})
        assert 'status' in result

    def test_arena_mode_long_prompt(self, arena_mode: OverwatchArenaMode):
        """Verify Arena Mode handles long prompts."""
        long_prompt = "a" * 10000
        results = arena_mode.compare_models(long_prompt, ["model1"])
        assert len(results) == 1

    def test_plan_mode_long_task(self, plan_mode: OverwatchPlanMode):
        """Verify Plan Mode handles long task descriptions."""
        long_task = "task: " + "detailed description " * 1000
        plan = plan_mode.create_plan(long_task)
        assert 'steps' in plan
