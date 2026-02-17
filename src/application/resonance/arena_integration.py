import ast
import logging
import operator
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Safe operators for rule evaluation
SAFE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda x, y: x and y,
    ast.Or: lambda x, y: x or y,
    ast.Not: operator.not_,
    ast.In: lambda x, y: x in y,
    ast.NotIn: lambda x, y: x not in y,
}

SAFE_FUNCTIONS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "min": min,
    "max": max,
}


def safe_eval_condition(condition: str, context: dict[str, Any]) -> bool:
    """
    Safely evaluate a condition string without using eval().

    This function uses AST parsing to safely evaluate boolean expressions
    with only whitelisted operations. It prevents code injection attacks
    while still allowing flexible rule conditions.

    Supported operations:
    - Comparisons: ==, !=, <, <=, >, >=
    - Boolean logic: and, or, not
    - Membership: in, not in
    - Safe functions: len, str, int, float, bool, abs, min, max

    Args:
        condition: Boolean expression string (e.g., "score > 100 and level == 5")
        context: Dictionary of available variables

    Returns:
        Boolean result of evaluation

    Raises:
        ValueError: If condition contains unsafe operations

    Security:
        - No eval() or exec()
        - No import statements
        - No function calls except whitelisted
        - No attribute access
        - No arbitrary code execution
    """
    try:
        # Parse condition into AST
        tree = ast.parse(condition, mode="eval")

        # Evaluate the AST node
        return _eval_node(tree.body, context)

    except Exception as e:
        logger.error(f"Failed to evaluate condition '{condition}': {e}")
        return False


def _eval_node(node: ast.AST, context: dict[str, Any]) -> Any:
    """
    Recursively evaluate an AST node with safety checks.

    Only allows whitelisted operations and functions.
    """
    # Literal values (numbers, strings, etc.)
    if isinstance(node, ast.Constant):
        return node.value

    # Variable lookup
    elif isinstance(node, ast.Name):
        if node.id not in context:
            raise ValueError(f"Variable '{node.id}' not found in context")
        return context[node.id]

    # Boolean operations (and, or)
    elif isinstance(node, ast.BoolOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(f"Operator {type(node.op).__name__} not allowed")

        # Evaluate left to right with short-circuit
        result = _eval_node(node.values[0], context)
        for value in node.values[1:]:
            result = op(result, _eval_node(value, context))
        return result

    # Comparison operations (==, !=, <, >, etc.)
    elif isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        result = True

        for op, comparator in zip(node.ops, node.comparators, strict=True):
            right = _eval_node(comparator, context)
            op_func = SAFE_OPERATORS.get(type(op))

            if not op_func:
                raise ValueError(f"Comparison operator {type(op).__name__} not allowed")

            result = result and op_func(left, right)
            left = right

        return result

    # Unary operations (not)
    elif isinstance(node, ast.UnaryOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(f"Unary operator {type(node.op).__name__} not allowed")

        operand = _eval_node(node.operand, context)
        return op(operand)

    # Function calls (only whitelisted)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")

        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' not allowed. Allowed: {list(SAFE_FUNCTIONS.keys())}")

        # Evaluate arguments
        args = [_eval_node(arg, context) for arg in node.args]

        # Call whitelisted function
        return SAFE_FUNCTIONS[func_name](*args)

    # List/tuple literals
    elif isinstance(node, (ast.List, ast.Tuple)):
        return [_eval_node(elt, context) for elt in node.elts]

    # Dictionary literals
    elif isinstance(node, ast.Dict):
        return {_eval_node(k, context): _eval_node(v, context) for k, v in zip(node.keys, node.values, strict=True)}

    else:
        raise ValueError(f"AST node type {type(node).__name__} not allowed for security reasons")


@dataclass
class Reward:
    name: str
    points: int


@dataclass
class Penalty:
    name: str
    points: int


@dataclass
class Rule:
    condition: str
    action: str  # 'reward' or 'penalty'
    target: str  # name of reward/penalty


@dataclass
class Goal:
    name: str
    target_score: int


class RewardSystem:
    def __init__(self):
        self.score = 0
        self.achievements: list[str] = []

    def apply_reward(self, reward: Reward):
        self.score += reward.points
        self.achievements.append(reward.name)


class PenaltySystem:
    def __init__(self):
        self.violations: list[str] = []

    def apply_penalty(self, penalty: Penalty, reward_system: RewardSystem):
        reward_system.score -= penalty.points
        self.violations.append(penalty.name)


class RuleEngine:
    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(self, context: dict[str, Any]) -> list[str]:
        """
        Evaluate rules against context using safe expression evaluation.

        Security: Uses AST-based parsing instead of eval() to prevent code injection.
        Only whitelisted operations and functions are allowed.
        """
        triggered_actions = []
        for rule in self.rules:
            try:
                # SECURITY: Using safe_eval_condition() instead of eval()
                # This prevents arbitrary code execution attacks
                if safe_eval_condition(rule.condition, context):
                    triggered_actions.append(rule.action)
            except ValueError as e:
                logger.error(f"Rule evaluation failed for condition '{rule.condition}': {e}")
                # Continue evaluating other rules even if one fails
                continue
        return triggered_actions


class GoalTracker:
    def __init__(self, goal: Goal):
        self.goal = goal

    def is_goal_reached(self, reward_system: RewardSystem) -> bool:
        return reward_system.score >= self.goal.target_score


class ArenaIntegration:
    def __init__(self, rules: list[Rule], goal: Goal, vortex: Any = None):
        self.reward_system = RewardSystem()
        self.penalty_system = PenaltySystem()
        self.rule_engine = RuleEngine(rules)
        self.goal_tracker = GoalTracker(goal)
        self.vortex = vortex

    def process_event(self, context: dict[str, Any]):
        actions = self.rule_engine.evaluate(context)
        impact = 0.5  # Baseline

        for action in actions:
            # Simplified logic
            if "REWARD" in action:
                self.reward_system.apply_reward(Reward("Sample Reward", 10))
                impact = 0.8
            elif "PENALTY" in action:
                self.penalty_system.apply_penalty(Penalty("Sample Penalty", 5), self.reward_system)
                impact = 0.8

        # Notify Vortex
        if self.vortex:
            import asyncio

            try:
                # Use call_soon_threadsafe if we are in a sync context but need to log to async vortex
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.vortex.log_event("ARENA_EVENT", {"context": context, "actions": actions}, impact=impact),
                        loop,
                    )
            except Exception as e:
                logger.warning(f"Failed to notify Databricks from Arena: {e}")
