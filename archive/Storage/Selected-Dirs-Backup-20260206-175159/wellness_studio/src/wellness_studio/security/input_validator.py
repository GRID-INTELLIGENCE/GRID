"""
Wellness Studio - Enhanced Input Validation Guardrails
Comprehensive input sanitization and validation
"""
import re
import json
import html
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from bleach import clean as bleach_clean


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    FILE_VALIDATION = "file_validation"
    SCHEMA_VALIDATION = "schema_validation"
    CONTENT_SANITIZE = "content_sanitize"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    sanitized: str
    issues: List[Dict[str, Any]]
    severity: str
    category: str


class InputValidator:
    """
    Comprehensive input validation and sanitization
    Protects against OWASP Top 10 injection attacks
    """
    
    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        r"[';]\s*(or|and)\s+['\"]?\w+['\"]?\s*[=<>!]+\s*['\"]?\w+['\"]?",
        r"[';]\s*(or|and)\s+\d+\s*[=<>!]+\s*\d+",
        r"union\s+select",
        r"drop\s+table",
        r"delete\s+from",
        r"insert\s+into",
        r"update\s+\w+\s+set",
        r"\b(exec|execute)\s*\(",
        r"\bwaitfor\s+delay",
        r"\bbenchmark\s*\(",
        r"--\s*$",
        r"#\s*$",
        r";\s*$",
        r"/\*\*.*?\*/",  # SQL comments
        r"union\s+/\*\*.*?\*/\s*select",  # UNION with comments
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"<style[^>]*>.*?</style>",
        r"expression\s*\(",
        r"fromCharCode",
        r"&#\d+;",
        r"&#x[0-9a-fA-F]+;",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",  # Shell metacharacters
        r"\|\s*\w+",   # Pipe with command
        r";\s*\w+",    # Semicolon with command
        r"&\s*\w+",    # Ampersand with command
        r"`[^`]*`",    # Backticks
        r"\$\([^)]*\)", # Command substitution
        r"&&\s*\w+",   # Double ampersand
        r"\|\|\s*\w+", # Double pipe
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%252e%252e%252f",
        r"/proc/self/environ",
        r"/proc/self/",
        r"windows\\system32",
        r"\\windows\\",
        r"\.\.%5c",
        r"%2e%2e%5c",
    ]
    
    # Allowed file extensions
    ALLOWED_FILE_EXTENSIONS = {
        '.txt', '.md', '.json', '.csv', '.pdf', '.doc', '.docx',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'
    }
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator
        
        Args:
            strict_mode: If True, blocks on critical issues. If False, warns only.
        """
        self.strict_mode = strict_mode
        self.validation_log: List[Dict] = []
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.compiled_sql = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.compiled_xss = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XSS_PATTERNS]
        self.compiled_command = [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INJECTION_PATTERNS]
        self.compiled_path = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
    
    def validate_input(
        self,
        input_data: str,
        context: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate input against all security threats
        
        Args:
            input_data: Input string to validate
            context: Optional context for validation
            
        Returns:
            ValidationResult with status and sanitized output
        """
        all_issues = []
        
        # Check SQL injection
        sql_issues = self._check_sql_injection(input_data)
        all_issues.extend(sql_issues)
        
        # Check XSS
        xss_issues = self._check_xss(input_data)
        all_issues.extend(xss_issues)
        
        # Check command injection
        cmd_issues = self._check_command_injection(input_data)
        all_issues.extend(cmd_issues)
        
        # Check path traversal
        path_issues = self._check_path_traversal(input_data)
        all_issues.extend(path_issues)
        
        # Sanitize content
        sanitized = self._sanitize_html(input_data)
        
        # Determine overall validity
        critical_issues = [i for i in all_issues if i['severity'] == ValidationSeverity.CRITICAL.value]
        error_issues = [i for i in all_issues if i['severity'] == ValidationSeverity.ERROR.value]
        is_valid = len(critical_issues) == 0 and len(error_issues) == 0
        
        # Determine max severity
        severities = [i['severity'] for i in all_issues]
        if ValidationSeverity.CRITICAL.value in severities:
            max_severity = ValidationSeverity.CRITICAL.value
        elif ValidationSeverity.ERROR.value in severities:
            max_severity = ValidationSeverity.ERROR.value
        elif ValidationSeverity.WARNING.value in severities:
            max_severity = ValidationSeverity.WARNING.value
        else:
            max_severity = ValidationSeverity.INFO.value
        
        result = ValidationResult(
            is_valid=is_valid,
            sanitized=sanitized,
            issues=all_issues,
            severity=max_severity,
            category='input_validation'
        )
        
        # Log validation
        self.validation_log.append({
            'timestamp': None,
            'context': context,
            'input_hash': hash(input_data) % 10000,
            'is_valid': is_valid,
            'issues_count': len(all_issues),
            'severity': max_severity
        })
        
        return result
    
    def _check_sql_injection(self, text: str) -> List[Dict[str, Any]]:
        """Check for SQL injection patterns"""
        issues = []
        
        for pattern in self.compiled_sql:
            match = pattern.search(text)
            if match:
                issues.append({
                    'category': ValidationCategory.SQL_INJECTION.value,
                    'severity': ValidationSeverity.CRITICAL.value,
                    'description': 'Potential SQL injection detected',
                    'detected_pattern': match.group(),
                    'recommendation': 'Use parameterized queries and input validation'
                })
        
        return issues
    
    def _check_xss(self, text: str) -> List[Dict[str, Any]]:
        """Check for XSS patterns"""
        issues = []
        
        for pattern in self.compiled_xss:
            match = pattern.search(text)
            if match:
                issues.append({
                    'category': ValidationCategory.XSS.value,
                    'severity': ValidationSeverity.CRITICAL.value,
                    'description': 'Potential XSS attack detected',
                    'detected_pattern': match.group(),
                    'recommendation': 'Sanitize HTML output and use Content Security Policy'
                })
        
        return issues
    
    def _check_command_injection(self, text: str) -> List[Dict[str, Any]]:
        """Check for command injection patterns"""
        issues = []
        
        for pattern in self.compiled_command:
            match = pattern.search(text)
            if match:
                issues.append({
                    'category': ValidationCategory.COMMAND_INJECTION.value,
                    'severity': ValidationSeverity.CRITICAL.value,
                    'description': 'Potential command injection detected',
                    'detected_pattern': match.group(),
                    'recommendation': 'Avoid shell commands with user input'
                })
        
        return issues
    
    def _check_path_traversal(self, text: str) -> List[Dict[str, Any]]:
        """Check for path traversal patterns"""
        issues = []
        
        for pattern in self.compiled_path:
            match = pattern.search(text)
            if match:
                issues.append({
                    'category': ValidationCategory.PATH_TRAVERSAL.value,
                    'severity': ValidationSeverity.ERROR.value,
                    'description': 'Potential path traversal detected',
                    'detected_pattern': match.group(),
                    'recommendation': 'Validate and sanitize file paths'
                })
        
        return issues
    
    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML content"""
        return bleach_clean(
            text,
            tags=[],
            attributes={},
            strip=True
        )
    
    def validate_file(
        self,
        file_path: str,
        file_size: int,
        file_type: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate file upload
        
        Args:
            file_path: Path to file
            file_size: Size in bytes
            file_type: MIME type
            
        Returns:
            ValidationResult
        """
        issues = []
        
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            issues.append({
                'category': ValidationCategory.FILE_VALIDATION.value,
                'severity': ValidationSeverity.ERROR.value,
                'description': f'File size exceeds limit ({file_size} > {self.MAX_FILE_SIZE})',
                'recommendation': 'Upload smaller file'
            })
        
        # Check file extension
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        
        if ext not in self.ALLOWED_FILE_EXTENSIONS:
            issues.append({
                'category': ValidationCategory.FILE_VALIDATION.value,
                'severity': ValidationSeverity.ERROR.value,
                'description': f'File type not allowed: {ext}',
                'recommendation': f'Allowed types: {", ".join(self.ALLOWED_FILE_EXTENSIONS)}'
            })
        
        is_valid = len([i for i in issues if i['severity'] in [ValidationSeverity.CRITICAL.value, ValidationSeverity.ERROR.value]]) == 0
        max_severity = 'error' if issues else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized=file_path,
            issues=issues,
            severity='error' if issues else 'info',
            category='file_validation'
        )
    
    def validate_json_schema(
        self,
        json_data: str,
        schema: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate JSON against schema
        
        Args:
            json_data: JSON string
            schema: Schema dictionary
            
        Returns:
            ValidationResult
        """
        issues = []
        
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            issues.append({
                'category': ValidationCategory.SCHEMA_VALIDATION.value,
                'severity': ValidationSeverity.ERROR.value,
                'description': f'Invalid JSON: {str(e)}',
                'recommendation': 'Provide valid JSON'
            })
            
            return ValidationResult(
                is_valid=False,
                sanitized='',
                issues=issues,
                severity='error',
                category='schema_validation'
            )
        
        # Basic schema validation
        for field, field_schema in schema.items():
            if field_schema.get('required', False) and field not in data:
                issues.append({
                    'category': ValidationCategory.SCHEMA_VALIDATION.value,
                    'severity': ValidationSeverity.ERROR.value,
                    'description': f'Required field missing: {field}',
                    'recommendation': 'Provide all required fields'
                })
            
            if field in data:
                expected_type = field_schema.get('type')
                if expected_type:
                    if expected_type == 'string' and not isinstance(data[field], str):
                        issues.append({
                            'category': ValidationCategory.SCHEMA_VALIDATION.value,
                            'severity': ValidationSeverity.ERROR.value,
                            'description': f'Field {field} should be string',
                            'recommendation': 'Provide correct type'
                        })
                    elif expected_type == 'number' and not isinstance(data[field], (int, float)):
                        issues.append({
                            'category': ValidationCategory.SCHEMA_VALIDATION.value,
                            'severity': ValidationSeverity.ERROR.value,
                            'description': f'Field {field} should be number',
                            'recommendation': 'Provide correct type'
                        })
        
        is_valid = len([i for i in issues if i['severity'] in [ValidationSeverity.CRITICAL.value, ValidationSeverity.ERROR.value]]) == 0
        max_severity = 'error' if issues else 'info'
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized=json.dumps(data),
            issues=issues,
            severity='error' if issues else 'info',
            category='schema_validation'
        )
    
    def sanitize_text(
        self,
        text: str,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize text input
        
        Args:
            text: Input text
            allow_html: Whether to allow HTML tags
            
        Returns:
            Sanitized text
        """
        if not allow_html:
            return self._sanitize_html(text)
        
        return bleach_clean(
            text,
            tags=['b', 'i', 'u', 'strong', 'em', 'p', 'br'],
            attributes={},
            strip=False
        )
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address
            
        Returns:
            True if valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number
            
        Returns:
            True if valid
        """
        pattern = r'^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
        return re.match(pattern, phone) is not None
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL string
            
        Returns:
            True if valid
        """
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation checks performed
        
        Returns:
            Validation summary statistics
        """
        return {
            'total_validations': len(self.validation_log),
            'valid_count': sum(1 for v in self.validation_log if v['is_valid']),
            'invalid_count': sum(1 for v in self.validation_log if not v['is_valid']),
            'by_severity': {
                'critical': sum(1 for v in self.validation_log if v['severity'] == 'critical'),
                'error': sum(1 for v in self.validation_log if v['severity'] == 'error'),
                'warning': sum(1 for v in self.validation_log if v['severity'] == 'warning'),
                'info': sum(1 for v in self.validation_log if v['severity'] == 'info')
            }
        }
    
    def clear_validation_log(self):
        """Clear validation log"""
        self.validation_log.clear()
