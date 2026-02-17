from scripts.git_topic_utils import build_branch_name, is_valid_branch_name


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
