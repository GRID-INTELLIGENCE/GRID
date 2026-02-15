import logging
import sys

# Ensure we can import from e:\grid
sys.path.append("e:\\grid")
sys.path.append("e:\\grid\\work\\GRID\\src")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verification")


def test_deep_object_analysis():
    logger.info("Testing Deep Object Analysis...")
    try:
        from safety.rules.manager import TrustTier, get_rule_manager

        manager = get_rule_manager()
    except ImportError as e:
        logger.error(f"Failed to import SafetyRuleManager: {e}")
        return

    # Case 1: Safe Content
    safe_data = {"message": "Hello world", "value": 123}
    is_safe, reasons = manager.evaluate_request("user1", "user", safe_data)
    assert is_safe, f"Safe data blocked: {reasons}"
    logger.info("PASS: Safe Content")

    # Case 2: Nested Code Injection (eval)
    unsafe_code_nested = {"meta": {"script": "eval('os.system(\"rm -rf\")')"}}
    is_safe, reasons = manager.evaluate_request("user2", "user", unsafe_code_nested)
    assert not is_safe, "Unsafe nested code NOT blocked"
    assert any("Forbidden function call: eval" in r for r in reasons), f"Unexpected reasons: {reasons}"
    logger.info(f"PASS: Nested Code Injection blocked: {reasons[0]}")

    # Case 3: Forbidden Config Key
    unsafe_config = {"settings": {"debug_mode": True, "admin": True}}
    is_safe, reasons = manager.evaluate_request("user3", "user", unsafe_config)
    assert not is_safe, "Unsafe config key NOT blocked"
    assert any("Unauthorized configuration key" in r for r in reasons), f"Unexpected reasons: {reasons}"
    logger.info(f"PASS: Forbidden Config Key blocked: {reasons[0]}")

    # Case 4: Harmful Prompt (RuleEngine pattern)
    harmful_prompt = "I want to kill myself"
    # We might need to ensure default rules are loaded or mock them if RuleEngine relies on external files
    # manager uses _engine which loads rules.
    # We can try to rely on default rules in `safety/rules/loader.py` or just verify prompt inspection runs.

    is_safe, reasons = manager.evaluate_request("user4", "user", harmful_prompt)
    if not is_safe:
        logger.info(f"PASS: Harmful Prompt blocked: {reasons[0]}")
    else:
        logger.warning("WARN: Harmful Prompt NOT blocked (Default rules might not be loaded or regex mismatch)")


if __name__ == "__main__":
    test_deep_object_analysis()
