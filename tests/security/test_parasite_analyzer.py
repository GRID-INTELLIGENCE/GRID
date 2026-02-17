import ast

from scripts.operations.parasite_analyzer import SecurityVisitor, whitelist


class TestSecurityVisitor:
    def _visit_code(self, code: str) -> list:
        tree = ast.parse(code)
        visitor = SecurityVisitor("test_file.py")
        visitor.visit(tree)
        return visitor.findings

    def test_detect_eval(self):
        code = "eval('print(1)')"
        findings = self._visit_code(code)
        assert len(findings) == 1
        assert findings[0]["risk"] == "HIGH"
        assert findings[0]["category"] == "dangerous_execution"
        assert "eval" in findings[0]["message"]

    def test_detect_subprocess_shell(self):
        code = "import subprocess\nsubprocess.call('ls', shell=True)"
        findings = self._visit_code(code)
        # Should find both the import and the call with shell=True
        # One for 'subprocess.call' (HIGH) and one for shell=True (CRITICAL)
        assert len(findings) >= 2
        risks = [f["risk"] for f in findings]
        assert "CRITICAL" in risks
        assert "HIGH" in risks

    def test_detect_suspicious_import(self):
        code = "import telnetlib"
        findings = self._visit_code(code)
        assert len(findings) == 1
        assert findings[0]["category"] == "suspicious_import"

    def test_detect_suspicious_import_from(self):
        code = "from telnetlib import Telnet"
        findings = self._visit_code(code)
        assert len(findings) == 1
        assert findings[0]["category"] == "suspicious_import"

    def test_detect_suspicious_function_name(self):
        code = "def hook_event():\n    pass"
        findings = self._visit_code(code)
        assert len(findings) == 1
        assert findings[0]["category"] == "suspicious_name"
        assert "hook" in findings[0]["message"]

    def test_safe_code_no_findings(self):
        code = "def calculate(a, b):\n    return a + b"
        findings = self._visit_code(code)
        assert len(findings) == 0

    def test_nested_eval(self):
        code = """
def run_dynamic():
    code = "1 + 1"
    return eval(code)
"""
        findings = self._visit_code(code)
        assert len(findings) == 1
        assert findings[0]["context"] == "run_dynamic"

    def test_whitelist_structure(self):
        # Basic check to ensure whitelist is defined
        assert isinstance(whitelist, dict)
        assert "subprocess" in whitelist
