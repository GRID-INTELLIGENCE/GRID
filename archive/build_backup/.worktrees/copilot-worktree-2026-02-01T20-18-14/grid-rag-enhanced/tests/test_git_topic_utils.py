import sys
from pathlib import Path

import pytest

# Allow importing scripts.git_topic_utils when repo root has scripts/
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from scripts.git_topic_utils import build_branch_name, is_valid_branch_name
except ImportError:
    pytest.skip("scripts.git_topic_utils not available (scripts/ not present)", allow_module_level=True)


def test_build_branch_simple():
    b = build_branch_name("research", "entity clustering", "123")
    assert b == "topic/research-entity-clustering-123"


def test_build_branch_no_issue():
    b = build_branch_name("infra", "add logging")
    assert b == "topic/infra-add-logging"


def test_is_valid_branch():
    assert is_valid_branch_name("topic/research-entity-clustering-123")
    assert is_valid_branch_name("topic/infra-add-logging")
    assert not is_valid_branch_name("feature/add-thing")
    assert not is_valid_branch_name("topic/InvalidChars!!")
