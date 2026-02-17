# parasite_analyzer.py
import ast
import dis
import importlib
import inspect
import json
import re
from pathlib import Path
from typing import Any


class ParasiteAnalyzer:
    def __init__(self):
        self.suspicious_patterns = {
            # Execution patterns
            "exec": re.compile(r"(?<!\.)exec\s*\(|eval\s*\(|compile\s*\("),
            "os_system": re.compile(r"os\.system\s*\("),
            "subprocess": re.compile(r"subprocess\.(run|call|Popen)\s*\("),
            "pickle": re.compile(r"pickle\.(loads?|dumps?)\s*\("),
            "yaml_unsafe": re.compile(r"yaml\.(load\s*\(|FullLoader\s*=\s*False)"),
            "deserialization": re.compile(r"(pickle|marshal|shelve|yaml|json)\.load"),
            # Network patterns
            "http": re.compile(r"http\.(client|server)|urllib|requests\.(get|post|put|delete)"),
            "socket": re.compile(r"socket\.(socket|create_connection)"),
            # File system patterns
            "file_ops": re.compile(r"open\s*\(|os\.(remove|unlink|rmdir|removedirs|makedirs|rename|replace)"),
            "path_traversal": re.compile(r"\.\./|/\.\./|/etc/passwd|/etc/shadow"),
            # Code injection patterns
            "dynamic_import": re.compile(r"__import__\s*\(|importlib\.import_module\s*\("),
            "code_objects": re.compile(r"code\s*\(|types\.CodeType\s*\("),
            "getattr_setattr": re.compile(r"(getattr|setattr|delattr|hasattr)\s*\("),
            "reflection": re.compile(r"globals\s*\(|locals\s*\(|vars\s*\("),
            # Obfuscation patterns
            "base64": re.compile(r"base64\.(b64encode|b64decode|urlsafe_b64decode)"),
            "codec_obfuscation": re.compile(r'\.encode\s*\(\s*[\'"]rot13|[\'"]base64|[\'"]hex'),
            # Memory manipulation
            "ctypes": re.compile(r"ctypes\.(cast|pointer|POINTER)"),
            "memoryview": re.compile(r"memoryview\s*\("),
            # Suspicious string patterns
            "suspicious_strings": re.compile(
                r"eval\(|exec\(|__import__|base64\.b64decode|getattr\("
                r"|os\.system|subprocess\.run|pickle\.loads?|yaml\.load"
            ),
        }

        self.whitelist = {
            "functions": {
                "os.path": ["join", "exists", "isdir", "isfile", "basename", "dirname"],
                "json": ["load", "loads", "dump", "dumps"],
                "yaml": ["safe_load", "safe_dump"],
                "pickle": ["dumps", "loads"],  # Only if properly sanitized
            },
            "modules": ["os", "sys", "json", "yaml", "pickle", "subprocess"],
        }

        self.analysis_results = {
            "suspicious_functions": [],
            "whitelist_violations": [],
            "code_quality_issues": [],
            "security_risks": [],
            "signature_analysis": [],
            "stats": {
                "total_functions": 0,
                "suspicious_functions": 0,
                "whitelist_violations": 0,
                "code_quality_issues": 0,
                "security_risks": 0,
            },
        }

    def analyze_function(self, func) -> dict[str, Any]:
        """Analyze a single function for suspicious patterns."""
        try:
            source = inspect.getsource(func)
            func_name = f"{func.__module__}.{func.__qualname__}"
            self.analysis_results["stats"]["total_functions"] += 1

            findings = {
                "function": func_name,
                "file": inspect.getsourcefile(func),
                "line": inspect.getsourcelines(func)[1],
                "patterns_found": [],
                "security_risk": False,
                "whitelist_violation": False,
                "code_quality_issue": False,
            }

            # Check for suspicious patterns
            for pattern_name, pattern in self.suspicious_patterns.items():
                if pattern.search(source):
                    findings["patterns_found"].append(pattern_name)
                    if pattern_name not in ["json", "yaml"]:  # These need context
                        findings["security_risk"] = True
                        self.analysis_results["stats"]["security_risks"] += 1

            # Check whitelist violations
            if self._check_whitelist_violation(func, source):
                findings["whitelist_violation"] = True
                self.analysis_results["stats"]["whitelist_violations"] += 1

            # Check code quality
            if self._check_code_quality_issues(func, source):
                findings["code_quality_issue"] = True
                self.analysis_results["stats"]["code_quality_issues"] += 1

            # Add to results if anything was found
            if (
                findings["patterns_found"]
                or findings["whitelist_violation"]
                or findings["code_quality_issue"]
                or findings["security_risk"]
            ):
                self.analysis_results["suspicious_functions"].append(findings)
                self.analysis_results["stats"]["suspicious_functions"] += 1

            return findings

        except (TypeError, OSError):
            # Skip built-in functions, C extensions, etc.
            return {}

    def _check_whitelist_violation(self, func, source: str) -> bool:
        """Check if function uses non-whitelisted functions/modules."""
        # Skip whitelist check for whitelisted modules
        module_name = func.__module__.split(".")[0]
        if module_name in self.whitelist["modules"]:
            return False

        for module, funcs in self.whitelist["functions"].items():
            for func_name in funcs:
                pattern = re.compile(rf"(?<!\.){re.escape(module)}\.{re.escape(func_name)}\s*\(")
                if pattern.search(source):
                    return True
        return False

    def _check_code_quality_issues(self, func, source: str) -> bool:
        """Check for code quality issues that might indicate problems."""
        issues = []

        # Check for overly complex functions
        try:
            code = compile(source, "<string>", "exec")
            instructions = list(dis.get_instructions(code))
            if len(instructions) > 200:  # Arbitrary threshold
                issues.append("function_too_complex")
        except:
            pass

        # Check for too many nested blocks
        if len(re.findall(r"(\{|\()\s*(?:\{|\()", source)) > 3:
            issues.append("too_many_nested_blocks")

        # Check for long parameter lists
        sig = inspect.signature(func)
        if len(sig.parameters) > 7:  # More than 7 parameters
            issues.append("too_many_parameters")

        return bool(issues)

    def analyze_module(self, module_name: str):
        """Analyze all functions in a module."""
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj):
                    self.analyze_function(obj)
                elif inspect.isclass(obj):
                    self.analyze_class(obj)
        except ImportError:
            print(f"⚠️ Could not import module: {module_name}")
        except Exception as e:
            print(f"❌ Error analyzing {module_name}: {str(e)}")

    def analyze_class(self, cls):
        """Analyze all methods in a class."""
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            self.analyze_function(method)

    def analyze_directory(self, directory: str):
        """Analyze all Python files in a directory recursively."""
        directory = Path(directory)
        for py_file in directory.rglob("*.py"):
            try:
                # Parse the file
                with open(py_file, encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue  # Skip files with syntax errors

                # Analyze each function in the file
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self._analyze_ast_function(node, py_file)

            except Exception as e:
                print(f"Error analyzing {py_file}: {str(e)}")

    def _analyze_ast_function(self, node, file_path: Path):
        """Analyze a function from AST node."""
        func_name = node.name
        source = ast.unparse(node)

        findings = {
            "function": func_name,
            "file": str(file_path),
            "line": node.lineno,
            "patterns_found": [],
            "security_risk": False,
            "whitelist_violation": False,
            "code_quality_issue": False,
        }

        # Check for suspicious patterns
        for pattern_name, pattern in self.suspicious_patterns.items():
            if pattern.search(source):
                findings["patterns_found"].append(pattern_name)
                if pattern_name not in ["json", "yaml"]:  # These need context
                    findings["security_risk"] = True
                    self.analysis_results["stats"]["security_risks"] += 1

        # Add to results if anything was found
        if (
            findings["patterns_found"]
            or findings["whitelist_violation"]
            or findings["code_quality_issue"]
            or findings["security_risk"]
        ):
            self.analysis_results["suspicious_functions"].append(findings)
            self.analysis_results["stats"]["suspicious_functions"] += 1
            self.analysis_results["stats"]["total_functions"] += 1

    def generate_report(self, output_file: str = "parasite_analysis_report.json"):
        """Generate a detailed report of findings."""
        # Sort findings by severity
        self.analysis_results["suspicious_functions"].sort(
            key=lambda x: (x["security_risk"], x["whitelist_violation"], x["code_quality_issue"]), reverse=True
        )

        # Save to file
        with open(output_file, "w") as f:
            json.dump(self.analysis_results, f, indent=2)

        return self.analysis_results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Python code for potential parasitic functions")
    parser.add_argument("target", help="Module, class, function, or directory to analyze")
    parser.add_argument(
        "--output", "-o", default="parasite_analysis_report.json", help="Output file for the analysis report"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Recursively analyze all Python files in a directory"
    )

    args = parser.parse_args()

    analyzer = ParasiteAnalyzer()

    if args.recursive:
        print(f"🔍 Analyzing directory recursively: {args.target}")
        analyzer.analyze_directory(args.target)
    else:
        try:
            # Try to import as a module
            module = importlib.import_module(args.target)
            if inspect.ismodule(module):
                print(f"🔍 Analyzing module: {args.target}")
                analyzer.analyze_module(args.target)
            elif inspect.isclass(module):
                print(f"🔍 Analyzing class: {args.target}")
                analyzer.analyze_class(module)
            elif inspect.isfunction(module):
                print(f"🔍 Analyzing function: {args.target}")
                analyzer.analyze_function(module)
            else:
                print(f"❌ Unsupported target type: {args.target}")
                return 1
        except ImportError:
            # If not importable, try as a file or directory
            path = Path(args.target)
            if path.is_file() and path.suffix == ".py":
                print(f"🔍 Analyzing file: {args.target}")
                analyzer.analyze_directory(path.parent)
            elif path.is_dir():
                print(f"🔍 Analyzing directory: {args.target}")
                analyzer.analyze_directory(args.target)
            else:
                print(f"❌ Could not analyze target: {args.target}")
                return 1

    # Generate and save report
    report = analyzer.generate_report(args.output)

    # Print summary
    print("\n=== Analysis Complete ===")
    print(f"📊 Total functions analyzed: {report['stats']['total_functions']}")
    print(f"⚠️  Suspicious functions: {report['stats']['suspicious_functions']}")
    print(f"🔒 Security risks: {report['stats']['security_risks']}")
    print(f"🚨 Whitelist violations: {report['stats']['whitelist_violations']}")
    print(f"🔍 Code quality issues: {report['stats']['code_quality_issues']}")
    print(f"\n📄 Full report saved to: {args.output}")


if __name__ == "__main__":
    main()
