"""
Comprehensive tests for Input Validation Guardrails
Tests SQL injection, XSS, command injection, and file validation
"""
import pytest
from wellness_studio.security import (
    InputValidator,
    ValidationResult,
    ValidationSeverity,
    ValidationCategory
)


class TestInputValidation:
    """Test input validation functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create input validator"""
        return InputValidator()
    
    def test_validate_clean_input(self, validator):
        """Test validating clean input"""
        result = validator.validate_input("Hello, World!")
        
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.sanitized == "Hello, World!"
    
    def test_detect_sql_injection(self, validator):
        """Test SQL injection detection"""
        malicious = "1' OR '1'='1"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any(i['category'] == ValidationCategory.SQL_INJECTION.value for i in result.issues)
    
    def test_detect_union_select_injection(self, validator):
        """Test UNION SELECT injection detection"""
        malicious = "1' UNION SELECT * FROM users--"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.SQL_INJECTION.value for i in result.issues)
    
    def test_detect_drop_table_injection(self, validator):
        """Test DROP TABLE injection detection"""
        malicious = "'; DROP TABLE users--"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.SQL_INJECTION.value for i in result.issues)
    
    def test_detect_xss_script(self, validator):
        """Test XSS script tag detection"""
        malicious = "<script>alert('XSS')</script>"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.XSS.value for i in result.issues)
    
    def test_detect_xss_javascript(self, validator):
        """Test javascript: protocol XSS detection"""
        malicious = "javascript:alert('XSS')"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.XSS.value for i in result.issues)
    
    def test_detect_xss_on_event(self, validator):
        """Test on* event XSS detection"""
        malicious = "<img src=x onerror=alert('XSS')>"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.XSS.value for i in result.issues)
    
    def test_detect_command_injection(self, validator):
        """Test command injection detection"""
        malicious = "file.txt; cat /etc/passwd"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.COMMAND_INJECTION.value for i in result.issues)
    
    def test_detect_pipe_command_injection(self, validator):
        """Test pipe command injection detection"""
        malicious = "file.txt | rm -rf /"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.COMMAND_INJECTION.value for i in result.issues)
    
    def test_detect_backtick_injection(self, validator):
        """Test backtick command injection detection"""
        malicious = "`whoami`"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.COMMAND_INJECTION.value for i in result.issues)
    
    def test_detect_path_traversal(self, validator):
        """Test path traversal detection"""
        malicious = "../../../etc/passwd"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.PATH_TRAVERSAL.value for i in result.issues)
    
    def test_detect_encoded_path_traversal(self, validator):
        """Test URL-encoded path traversal detection"""
        malicious = "%2e%2e%2fetc%2fpasswd"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.PATH_TRAVERSAL.value for i in result.issues)
    
    def test_sanitize_html(self, validator):
        """Test HTML sanitization"""
        input_text = "<script>alert('XSS')</script><b>bold</b>"
        sanitized = validator.sanitize_text(input_text)
        
        assert "<script>" not in sanitized
        assert "XSS" in sanitized  # Text content remains
        assert "bold" in sanitized
    
    def test_sanitize_text_allow_html(self, validator):
        """Test sanitization with HTML allowed"""
        input_text = "<script>alert('XSS')</script><b>bold</b>"
        sanitized = validator.sanitize_text(input_text, allow_html=True)
        
        assert "<script>" not in sanitized
        assert "<b>" in sanitized
    
    def test_validate_file_allowed_type(self, validator):
        """Test validating allowed file type"""
        result = validator.validate_file(
            file_path="document.pdf",
            file_size=1024,
            file_type="application/pdf"
        )
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validate_file_disallowed_type(self, validator):
        """Test validating disallowed file type"""
        result = validator.validate_file(
            file_path="malware.exe",
            file_size=1024,
            file_type="application/x-msdownload"
        )
        
        assert result.is_valid is False
        assert len(result.issues) > 0
    
    def test_validate_file_too_large(self, validator):
        """Test validating file size limit"""
        result = validator.validate_file(
            file_path="large_file.pdf",
            file_size=100 * 1024 * 1024,  # 100MB
            file_type="application/pdf"
        )
        
        assert result.is_valid is False
        assert any('size' in i['description'].lower() for i in result.issues)
    
    def test_validate_json_schema_valid(self, validator):
        """Test validating JSON against schema (valid)"""
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "number", "required": False}
        }
        json_data = '{"name": "John Doe", "age": 35}'
        
        result = validator.validate_json_schema(json_data, schema)
        
        assert result.is_valid is True
    
    def test_validate_json_schema_missing_required(self, validator):
        """Test validating JSON with missing required field"""
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "number", "required": False}
        }
        json_data = '{"age": 35}'
        
        result = validator.validate_json_schema(json_data, schema)
        
        assert result.is_valid is False
        assert any('required' in i['description'].lower() for i in result.issues)
    
    def test_validate_json_schema_invalid_json(self, validator):
        """Test validating invalid JSON"""
        schema = {"name": {"type": "string", "required": True}}
        json_data = '{invalid json}'
        
        result = validator.validate_json_schema(json_data, schema)
        
        assert result.is_valid is False
        assert any('invalid json' in i['description'].lower() for i in result.issues)
    
    def test_validate_email_valid(self, validator):
        """Test validating valid email"""
        assert validator.validate_email("user@example.com") is True
        assert validator.validate_email("test.user+tag@example.co.uk") is True
    
    def test_validate_email_invalid(self, validator):
        """Test validating invalid email"""
        assert validator.validate_email("invalid") is False
        assert validator.validate_email("@example.com") is False
        assert validator.validate_email("user@") is False
    
    def test_validate_phone_valid(self, validator):
        """Test validating valid phone numbers"""
        assert validator.validate_phone("123-456-7890") is True
        assert validator.validate_phone("(123) 456-7890") is True
        assert validator.validate_phone("+1 123-456-7890") is True
    
    def test_validate_phone_invalid(self, validator):
        """Test validating invalid phone numbers"""
        assert validator.validate_phone("123") is False
        assert validator.validate_phone("abc-def-ghij") is False
    
    def test_validate_url_valid(self, validator):
        """Test validating valid URLs"""
        assert validator.validate_url("https://example.com") is True
        assert validator.validate_url("http://example.com/path") is True
    
    def test_validate_url_invalid(self, validator):
        """Test validating invalid URLs"""
        assert validator.validate_url("not-a-url") is False
        assert validator.validate_url("ftp://example.com") is False
    
    def test_multiple_threats_detection(self, validator):
        """Test detecting multiple threats in one input"""
        malicious = "<script>alert('XSS')</script>'; DROP TABLE users--"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert len(result.issues) >= 2
    
    def test_validation_severity_levels(self, validator):
        """Test different severity levels"""
        critical_result = validator.validate_input("<script>alert('XSS')</script>")
        assert critical_result.severity == ValidationSeverity.CRITICAL.value
        
        clean_result = validator.validate_input("Hello, World!")
        assert clean_result.severity == ValidationSeverity.INFO.value
    
    def test_validation_logging(self, validator):
        """Test that validation is logged"""
        validator.validate_input("test input")
        
        summary = validator.get_validation_summary()
        
        assert summary['total_validations'] >= 1
    
    def test_clear_validation_log(self, validator):
        """Test clearing validation log"""
        validator.validate_input("test input")
        validator.clear_validation_log()
        
        summary = validator.get_validation_summary()
        
        assert summary['total_validations'] == 0
    
    def test_validation_summary(self, validator):
        """Test validation summary statistics"""
        validator.validate_input("clean input")
        validator.validate_input("<script>alert('XSS')</script>")
        
        summary = validator.get_validation_summary()
        
        assert summary['total_validations'] >= 2
        assert summary['valid_count'] >= 1
        assert summary['invalid_count'] >= 1
    
    def test_strict_mode(self, validator):
        """Test strict mode behavior"""
        assert validator.strict_mode is True
        
        non_strict = InputValidator(strict_mode=False)
        assert non_strict.strict_mode is False
    
    def test_empty_input(self, validator):
        """Test validating empty input"""
        result = validator.validate_input("")
        
        assert result.is_valid is True
        assert result.sanitized == ""
    
    def test_unicode_input(self, validator):
        """Test validating unicode input"""
        result = validator.validate_input("Hello 世界 🌍")
        
        assert result.is_valid is True
    
    def test_very_long_input(self, validator):
        """Test validating very long input"""
        long_input = "x" * 100000
        result = validator.validate_input(long_input)
        
        assert result.is_valid is True


class TestOWASPTop10:
    """Test protection against OWASP Top 10 vulnerabilities"""
    
    @pytest.fixture
    def validator(self):
        """Create input validator"""
        return InputValidator()
    
    def test_a1_injection_sql(self, validator):
        """Test A1:2021 - Injection (SQL)"""
        malicious = "1' OR '1'='1"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.SQL_INJECTION.value for i in result.issues)
    
    def test_a3_injection_xss(self, validator):
        """Test A3:2021 - Injection (XSS)"""
        malicious = "<script>alert('XSS')</script>"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.XSS.value for i in result.issues)
    
    def test_a1_command_injection(self, validator):
        """Test A1:2021 - Injection (Command)"""
        malicious = "file.txt; cat /etc/passwd"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.COMMAND_INJECTION.value for i in result.issues)
    
    def test_a1_path_traversal(self, validator):
        """Test A1:2021 - Injection (Path Traversal)"""
        malicious = "../../../etc/passwd"
        result = validator.validate_input(malicious)
        
        assert result.is_valid is False
        assert any(i['category'] == ValidationCategory.PATH_TRAVERSAL.value for i in result.issues)
    
    def test_a5_security_misconfiguration_file_upload(self, validator):
        """Test A5:2021 - Security Misconfiguration (File Upload)"""
        result = validator.validate_file(
            file_path="malware.exe",
            file_size=1024
        )
        
        assert result.is_valid is False
    
    def test_a3_xss_variations(self, validator):
        """Test various XSS attack patterns"""
        xss_attacks = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
            "<svg onload=alert('XSS')>",
            "expression(alert('XSS'))"
        ]
        
        for attack in xss_attacks:
            result = validator.validate_input(attack)
            assert result.is_valid is False, f"Should block: {attack}"
