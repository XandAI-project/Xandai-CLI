"""
Code Review Rules - Pattern-based analysis rules for different programming languages

This module contains structured rule definitions for static code analysis across
multiple programming languages. Rules are organized by language and severity.
"""

from typing import Callable, Dict, List


class ReviewRules:
    """Centralized repository of code review rules"""

    @staticmethod
    def get_rules_for_language(file_ext: str) -> List[Dict]:
        """
        Get analysis rules for a specific file extension

        Args:
            file_ext: File extension (e.g., 'py', 'js', 'ts')

        Returns:
            List of rule dictionaries with conditions and actions
        """
        rules_map = {
            "py": ReviewRules.get_python_rules(),
            "js": ReviewRules.get_javascript_rules(),
            "ts": ReviewRules.get_typescript_rules(),
            "jsx": ReviewRules.get_react_rules(),
            "tsx": ReviewRules.get_react_rules(),
            "java": ReviewRules.get_java_rules(),
            "cpp": ReviewRules.get_cpp_rules(),
            "c": ReviewRules.get_c_rules(),
            "php": ReviewRules.get_php_rules(),
            "rb": ReviewRules.get_ruby_rules(),
            "go": ReviewRules.get_go_rules(),
        }

        return rules_map.get(file_ext, ReviewRules.get_general_rules())

    @staticmethod
    def get_python_rules() -> List[Dict]:
        """Python-specific analysis rules"""
        return [
            {
                "name": "subprocess_shell_injection",
                "condition": lambda line, stripped, num: "subprocess.run(" in line
                and "shell=True" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Security risk - shell injection vulnerability",
                    "formatted_comment": f"Line {num}: Security risk - avoid shell=True in subprocess calls\n    Code: `{stripped}`\n    Suggestion: Use shell=False and pass command as list\n    Risk: Shell injection attacks possible",
                    "suggestion": f"Fix shell injection vulnerability in {path}",
                },
            },
            {
                "name": "bare_except",
                "condition": lambda line, stripped, num: "except:" in line
                and "except Exception" not in line
                and "except (" not in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Overly broad exception handling",
                    "formatted_comment": f"Line {num}: Use specific exception types instead of bare except\n    Code: `{stripped}`\n    Suggestion: Use 'except SpecificException as e:' or 'except Exception as e:'\n    Issue: Catches system exits and keyboard interrupts",
                    "suggestion": f"Improve exception handling specificity in {path}",
                },
            },
            {
                "name": "hardcoded_secrets",
                "condition": lambda line, stripped, num: any(
                    secret in line.lower() for secret in ["password", "api_key", "secret", "token"]
                )
                and "=" in line
                and ('"' in line or "'" in line),
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Potential hardcoded credentials",
                    "formatted_comment": f"Line {num}: Potential hardcoded password or sensitive data\n    Code: `{stripped}`\n    Suggestion: Move sensitive data to environment variables or secure config\n    Security: Never commit credentials to code",
                    "suggestion": f"Move hardcoded credentials to environment variables in {path}",
                },
            },
            {
                "name": "sql_injection_risk",
                "condition": lambda line, stripped, num: ("execute(" in line or "query(" in line)
                and ('"' in line or "'" in line)
                and "%" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Potential SQL injection vulnerability",
                    "formatted_comment": f"Line {num}: Potential SQL injection risk with string formatting\n    Code: `{stripped}`\n    Suggestion: Use parameterized queries or ORM methods\n    Risk: SQL injection attacks possible",
                    "suggestion": f"Implement parameterized queries in {path}",
                },
            },
            {
                "name": "print_statements",
                "condition": lambda line, stripped, num: "print(" in line
                and "debug" not in line.lower()
                and "test" not in line.lower(),
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Debug print statement",
                    "formatted_comment": f"Line {num}: Consider replacing print with proper logging\n    Code: `{stripped}`\n    Suggestion: Use logging.info(), logging.debug(), or logger methods\n    Benefit: Better log management and filtering",
                    "suggestion": f"Replace print statements with logging in {path}",
                },
            },
            {
                "name": "eval_usage",
                "condition": lambda line, stripped, num: "eval(" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Dangerous eval() usage",
                    "formatted_comment": f"Line {num}: Avoid using eval() - severe security risk\n    Code: `{stripped}`\n    Suggestion: Use ast.literal_eval() or alternative approaches\n    Risk: Code injection and arbitrary code execution",
                    "suggestion": f"Remove eval() usage in {path}",
                },
            },
            {
                "name": "exec_usage",
                "condition": lambda line, stripped, num: "exec(" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Dangerous exec() usage",
                    "formatted_comment": f"Line {num}: Avoid using exec() - severe security risk\n    Code: `{stripped}`\n    Suggestion: Refactor to use safer alternatives\n    Risk: Arbitrary code execution",
                    "suggestion": f"Remove exec() usage in {path}",
                },
            },
        ]

    @staticmethod
    def get_javascript_rules() -> List[Dict]:
        """JavaScript-specific analysis rules"""
        return [
            {
                "name": "var_usage",
                "condition": lambda line, stripped, num: "var " in line
                and not line.strip().startswith("//"),
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Outdated variable declaration",
                    "formatted_comment": f"Line {num}: Use 'const' or 'let' instead of 'var'\n    Code: `{stripped}`\n    Suggestion: Replace 'var' with 'const' for immutable or 'let' for mutable\n    Issue: 'var' has function scope and hoisting issues",
                    "suggestion": f"Modernize variable declarations in {path}",
                },
            },
            {
                "name": "xss_risk",
                "condition": lambda line, stripped, num: "innerHTML" in line and "=" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: XSS vulnerability with innerHTML",
                    "formatted_comment": f"Line {num}: Potential XSS risk with innerHTML\n    Code: `{stripped}`\n    Suggestion: Use textContent or sanitize HTML content\n    Risk: Cross-site scripting attacks possible",
                    "suggestion": f"Sanitize HTML input or use textContent in {path}",
                },
            },
            {
                "name": "loose_equality",
                "condition": lambda line, stripped, num: ("==" in line or "!=" in line)
                and ("===" not in line and "!==" not in line),
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Loose equality comparison",
                    "formatted_comment": f"Line {num}: Use strict equality\n    Code: `{stripped}`\n    Suggestion: Use === or !== for strict equality\n    Issue: Loose equality can cause unexpected type coercion",
                    "suggestion": f"Use strict equality operators in {path}",
                },
            },
            {
                "name": "console_log",
                "condition": lambda line, stripped, num: "console.log(" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Debug console statement",
                    "formatted_comment": f"Line {num}: Remove console.log in production code\n    Code: `{stripped}`\n    Suggestion: Use proper logging library or remove debug statements\n    Issue: Console statements can expose sensitive information",
                    "suggestion": f"Remove console.log statements in {path}",
                },
            },
            {
                "name": "eval_usage_js",
                "condition": lambda line, stripped, num: "eval(" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Dangerous eval() usage",
                    "formatted_comment": f"Line {num}: Avoid eval() - security vulnerability\n    Code: `{stripped}`\n    Suggestion: Use JSON.parse() or alternative approaches\n    Risk: Code injection attacks",
                    "suggestion": f"Remove eval() usage in {path}",
                },
            },
        ]

    @staticmethod
    def get_typescript_rules() -> List[Dict]:
        """TypeScript-specific rules"""
        js_rules = ReviewRules.get_javascript_rules()
        ts_specific = [
            {
                "name": "any_type",
                "condition": lambda line, stripped, num: ": any" in line or "<any>" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Using 'any' type defeats TypeScript purpose",
                    "formatted_comment": f"Line {num}: Avoid using 'any' type\n    Code: `{stripped}`\n    Suggestion: Use specific types or interfaces\n    Issue: 'any' removes type safety benefits",
                    "suggestion": f"Replace 'any' types with specific types in {path}",
                },
            },
            {
                "name": "ts_ignore",
                "condition": lambda line, stripped, num: "@ts-ignore" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: TypeScript error suppression",
                    "formatted_comment": f"Line {num}: Avoid @ts-ignore comments\n    Code: `{stripped}`\n    Suggestion: Fix the type error properly or use @ts-expect-error with explanation\n    Issue: Hides potential type safety issues",
                    "suggestion": f"Address type errors instead of suppressing in {path}",
                },
            },
        ]
        return js_rules + ts_specific

    @staticmethod
    def get_react_rules() -> List[Dict]:
        """React-specific rules"""
        js_rules = ReviewRules.get_javascript_rules()
        react_specific = [
            {
                "name": "missing_key_prop",
                "condition": lambda line, stripped, num: ".map(" in line
                and "key=" not in line
                and "=>" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Missing key prop in map",
                    "formatted_comment": f"Line {num}: Missing key prop in React list\n    Code: `{stripped}`\n    Suggestion: Add unique key prop to mapped elements\n    Issue: Can cause rendering performance issues",
                    "suggestion": f"Add key props to mapped React elements in {path}",
                },
            },
            {
                "name": "inline_styles",
                "condition": lambda line, stripped, num: "style={{" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Inline styles detected",
                    "formatted_comment": f"Line {num}: Consider CSS modules or styled-components\n    Code: `{stripped}`\n    Suggestion: Extract styles for better performance and maintainability\n    Issue: Inline styles are created on every render",
                    "suggestion": f"Extract inline styles to CSS or styled-components in {path}",
                },
            },
        ]
        return js_rules + react_specific

    @staticmethod
    def get_java_rules() -> List[Dict]:
        """Java-specific rules"""
        return ReviewRules.get_general_rules() + [
            {
                "name": "system_out_print",
                "condition": lambda line, stripped, num: "System.out.print" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Debug print statement",
                    "formatted_comment": f"Line {num}: Use proper logging framework\n    Code: `{stripped}`\n    Suggestion: Use SLF4J, Log4j, or java.util.logging\n    Issue: System.out is not suitable for production logging",
                    "suggestion": f"Replace System.out with logging framework in {path}",
                },
            }
        ]

    @staticmethod
    def get_cpp_rules() -> List[Dict]:
        """C++-specific rules"""
        return ReviewRules.get_general_rules() + [
            {
                "name": "raw_pointers",
                "condition": lambda line, stripped, num: "new " in line
                and "unique_ptr" not in line
                and "shared_ptr" not in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Raw pointer usage",
                    "formatted_comment": f"Line {num}: Consider smart pointers\n    Code: `{stripped}`\n    Suggestion: Use std::unique_ptr or std::shared_ptr\n    Issue: Manual memory management risks leaks",
                    "suggestion": f"Use smart pointers in {path}",
                },
            }
        ]

    @staticmethod
    def get_c_rules() -> List[Dict]:
        """C-specific rules"""
        return ReviewRules.get_general_rules() + [
            {
                "name": "gets_usage",
                "condition": lambda line, stripped, num: "gets(" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Dangerous gets() usage",
                    "formatted_comment": f"Line {num}: Never use gets() - buffer overflow risk\n    Code: `{stripped}`\n    Suggestion: Use fgets() instead\n    Risk: Buffer overflow vulnerability",
                    "suggestion": f"Replace gets() with fgets() in {path}",
                },
            }
        ]

    @staticmethod
    def get_php_rules() -> List[Dict]:
        """PHP-specific rules"""
        return ReviewRules.get_general_rules() + [
            {
                "name": "eval_usage_php",
                "condition": lambda line, stripped, num: "eval(" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "critical",
                    "message": f"Line {num}: Dangerous eval() usage",
                    "formatted_comment": f"Line {num}: Avoid eval() in PHP\n    Code: `{stripped}`\n    Suggestion: Refactor to use safer alternatives\n    Risk: Remote code execution vulnerability",
                    "suggestion": f"Remove eval() usage in {path}",
                },
            }
        ]

    @staticmethod
    def get_ruby_rules() -> List[Dict]:
        """Ruby-specific rules"""
        return ReviewRules.get_general_rules()

    @staticmethod
    def get_go_rules() -> List[Dict]:
        """Go-specific rules"""
        return ReviewRules.get_general_rules() + [
            {
                "name": "error_not_checked",
                "condition": lambda line, stripped, num: ", err :=" in line or ", err =" in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Error handling check needed",
                    "formatted_comment": f"Line {num}: Ensure error is properly handled\n    Code: `{stripped}`\n    Suggestion: Add 'if err != nil' check immediately after\n    Issue: Unchecked errors can cause unexpected behavior",
                    "suggestion": f"Add proper error handling in {path}",
                },
            }
        ]

    @staticmethod
    def get_general_rules() -> List[Dict]:
        """General rules applicable to all file types"""
        return [
            {
                "name": "long_lines",
                "condition": lambda line, stripped, num: len(stripped) > 120,
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Line too long",
                    "formatted_comment": f"Line {num}: Line too long ({len(stripped)} chars)\n    Code: `{stripped[:80]}...`\n    Suggestion: Break into multiple lines or extract to variable\n    Standard: Keep lines under 100-120 characters",
                    "suggestion": f"Break long lines for better readability in {path}",
                },
            },
            {
                "name": "todo_comments",
                "condition": lambda line, stripped, num: any(
                    marker in line.upper() for marker in ["TODO", "FIXME", "HACK", "XXX", "BUG"]
                ),
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Technical debt marker",
                    "formatted_comment": f"Line {num}: Code comment needs attention\n    Code: `{stripped}`\n    Action: Address technical debt or create issue\n    Markers: TODO, FIXME, HACK, XXX, BUG",
                    "suggestion": f"Address technical debt markers in {path}",
                },
            },
            {
                "name": "http_urls",
                "condition": lambda line, stripped, num: "http://" in line
                and "localhost" not in line,
                "action": lambda line, stripped, num, path: {
                    "severity": "medium",
                    "message": f"Line {num}: Insecure HTTP URL",
                    "formatted_comment": f"Line {num}: HTTP URL detected\n    Code: `{stripped}`\n    Suggestion: Use HTTPS for security\n    Issue: HTTP traffic is unencrypted",
                    "suggestion": f"Replace HTTP URLs with HTTPS in {path}",
                },
            },
            {
                "name": "commented_code",
                "condition": lambda line, stripped, num: stripped.startswith("#")
                and any(
                    code_pattern in stripped
                    for code_pattern in ["def ", "class ", "if ", "for ", "return ", "="]
                ),
                "action": lambda line, stripped, num, path: {
                    "severity": "low",
                    "message": f"Line {num}: Commented-out code",
                    "formatted_comment": f"Line {num}: Remove commented-out code\n    Code: `{stripped}`\n    Suggestion: Use version control instead of commenting code\n    Issue: Clutters codebase and reduces readability",
                    "suggestion": f"Remove commented code in {path}",
                },
            },
        ]
