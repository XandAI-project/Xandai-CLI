"""
Tests for Review Rules Module
Tests the centralized rule system for code analysis
"""

import pytest

from xandai.utils.review_rules import ReviewRules


class TestReviewRulesModule:
    """Test suite for ReviewRules module"""

    def test_get_rules_for_all_languages(self):
        """Test that rules can be retrieved for all supported languages"""
        languages = ["py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "php", "rb", "go"]

        for lang in languages:
            rules = ReviewRules.get_rules_for_language(lang)
            assert isinstance(rules, list), f"Rules for {lang} should be a list"
            assert len(rules) > 0, f"Rules for {lang} should not be empty"

    def test_unknown_language_fallback(self):
        """Test that unknown languages fall back to general rules"""
        rules = ReviewRules.get_rules_for_language("xyz")
        assert isinstance(rules, list)
        assert len(rules) > 0, "Should return general rules for unknown language"

    def test_rule_structure(self):
        """Test that all rules have required structure"""
        rules = ReviewRules.get_python_rules()

        for rule in rules:
            assert "name" in rule, "Rule must have 'name'"
            assert "condition" in rule, "Rule must have 'condition'"
            assert "action" in rule, "Rule must have 'action'"
            assert callable(rule["condition"]), "Condition must be callable"
            assert callable(rule["action"]), "Action must be callable"

    def test_python_rules_exist(self):
        """Test that Python-specific rules are defined"""
        rules = ReviewRules.get_python_rules()
        rule_names = [rule["name"] for rule in rules]

        # Check for critical security rules
        assert "subprocess_shell_injection" in rule_names
        assert "bare_except" in rule_names
        assert "hardcoded_secrets" in rule_names
        assert "sql_injection_risk" in rule_names
        assert "eval_usage" in rule_names
        assert "exec_usage" in rule_names

    def test_javascript_rules_exist(self):
        """Test that JavaScript-specific rules are defined"""
        rules = ReviewRules.get_javascript_rules()
        rule_names = [rule["name"] for rule in rules]

        assert "var_usage" in rule_names
        assert "xss_risk" in rule_names
        assert "loose_equality" in rule_names
        assert "console_log" in rule_names

    def test_general_rules_exist(self):
        """Test that general rules are defined"""
        rules = ReviewRules.get_general_rules()
        rule_names = [rule["name"] for rule in rules]

        assert "long_lines" in rule_names
        assert "todo_comments" in rule_names
        assert "http_urls" in rule_names


class TestPythonRules:
    """Test Python-specific rules"""

    def test_subprocess_shell_injection_detection(self):
        """Test shell injection vulnerability detection"""
        rules = ReviewRules.get_python_rules()
        shell_rule = next(r for r in rules if r["name"] == "subprocess_shell_injection")

        # Should trigger
        test_line = "subprocess.run('ls -la', shell=True)"
        assert shell_rule["condition"](test_line, test_line.strip(), 1)

        # Should not trigger
        safe_line = "subprocess.run(['ls', '-la'], shell=False)"
        assert not shell_rule["condition"](safe_line, safe_line.strip(), 1)

    def test_bare_except_detection(self):
        """Test bare except clause detection"""
        rules = ReviewRules.get_python_rules()
        except_rule = next(r for r in rules if r["name"] == "bare_except")

        # Should trigger
        test_line = "except:"
        assert except_rule["condition"](test_line, test_line.strip(), 1)

        # Should not trigger
        safe_line = "except Exception as e:"
        assert not safe_line or not except_rule["condition"](safe_line, safe_line.strip(), 1)

    def test_hardcoded_secrets_detection(self):
        """Test hardcoded secrets detection"""
        rules = ReviewRules.get_python_rules()
        secrets_rule = next(r for r in rules if r["name"] == "hardcoded_secrets")

        # Should trigger
        test_cases = [
            'password = "secret123"',
            'API_KEY = "sk-1234567890"',
            'token = "abc123def456"',
        ]

        for test_line in test_cases:
            assert secrets_rule["condition"](
                test_line, test_line.strip(), 1
            ), f"Should detect hardcoded secret in: {test_line}"

    def test_sql_injection_detection(self):
        """Test SQL injection vulnerability detection"""
        rules = ReviewRules.get_python_rules()
        sql_rule = next(r for r in rules if r["name"] == "sql_injection_risk")

        # Should trigger
        test_line = 'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
        assert sql_rule["condition"](test_line, test_line.strip(), 1)

        # Should not trigger (parameterized query)
        safe_line = 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))'
        assert not sql_rule["condition"](safe_line, safe_line.strip(), 1)

    def test_eval_exec_detection(self):
        """Test eval/exec usage detection"""
        rules = ReviewRules.get_python_rules()

        eval_rule = next(r for r in rules if r["name"] == "eval_usage")
        exec_rule = next(r for r in rules if r["name"] == "exec_usage")

        # Should trigger
        assert eval_rule["condition"]("result = eval(user_input)", "result = eval(user_input)", 1)
        assert exec_rule["condition"]("exec(code_string)", "exec(code_string)", 1)

    def test_rule_action_format(self):
        """Test that rule actions return proper format"""
        rules = ReviewRules.get_python_rules()
        rule = rules[0]

        test_line = "subprocess.run('ls', shell=True)"
        result = rule["action"](test_line, test_line.strip(), 42, "test.py")

        assert "severity" in result
        assert "message" in result
        assert "formatted_comment" in result
        assert result["severity"] in ["critical", "medium", "low"]
        assert "Line 42" in result["message"]


class TestJavaScriptRules:
    """Test JavaScript-specific rules"""

    def test_var_usage_detection(self):
        """Test outdated var keyword detection"""
        rules = ReviewRules.get_javascript_rules()
        var_rule = next(r for r in rules if r["name"] == "var_usage")

        # Should trigger
        assert var_rule["condition"]("var x = 10;", "var x = 10;", 1)

        # Should not trigger
        assert not var_rule["condition"]("const x = 10;", "const x = 10;", 1)
        assert not var_rule["condition"]("let x = 10;", "let x = 10;", 1)

    def test_xss_risk_detection(self):
        """Test XSS vulnerability detection"""
        rules = ReviewRules.get_javascript_rules()
        xss_rule = next(r for r in rules if r["name"] == "xss_risk")

        # Should trigger
        test_line = "element.innerHTML = userInput;"
        assert xss_rule["condition"](test_line, test_line.strip(), 1)

        # Should not trigger
        safe_line = "element.textContent = userInput;"
        assert not xss_rule["condition"](safe_line, safe_line.strip(), 1)

    def test_loose_equality_detection(self):
        """Test loose equality operator detection"""
        rules = ReviewRules.get_javascript_rules()
        equality_rule = next(r for r in rules if r["name"] == "loose_equality")

        # Should trigger
        assert equality_rule["condition"]("if (x == y)", "if (x == y)", 1)
        assert equality_rule["condition"]("if (x != y)", "if (x != y)", 1)

        # Should not trigger
        assert not equality_rule["condition"]("if (x === y)", "if (x === y)", 1)


class TestGeneralRules:
    """Test general rules applicable to all languages"""

    def test_long_lines_detection(self):
        """Test long line detection"""
        rules = ReviewRules.get_general_rules()
        long_line_rule = next(r for r in rules if r["name"] == "long_lines")

        # Should trigger
        long_line = "x" * 130
        assert long_line_rule["condition"](long_line, long_line.strip(), 1)

        # Should not trigger
        short_line = "x" * 50
        assert not long_line_rule["condition"](short_line, short_line.strip(), 1)

    def test_todo_comments_detection(self):
        """Test TODO/FIXME marker detection"""
        rules = ReviewRules.get_general_rules()
        todo_rule = next(r for r in rules if r["name"] == "todo_comments")

        markers = ["TODO", "FIXME", "HACK", "XXX", "BUG"]

        for marker in markers:
            test_line = f"# {marker}: Fix this later"
            assert todo_rule["condition"](
                test_line, test_line.strip(), 1
            ), f"Should detect {marker} marker"

    def test_http_urls_detection(self):
        """Test insecure HTTP URL detection"""
        rules = ReviewRules.get_general_rules()
        http_rule = next(r for r in rules if r["name"] == "http_urls")

        # Should trigger
        assert http_rule["condition"]('url = "http://example.com"', 'url = "http://example.com"', 1)

        # Should not trigger (localhost is excluded)
        assert (
            http_rule["condition"](
                'url = "http://localhost:3000"', 'url = "http://localhost:3000"', 1
            )
            == False
        )

        # Should not trigger (HTTPS)
        assert not http_rule["condition"](
            'url = "https://example.com"', 'url = "https://example.com"', 1
        )


class TestTypeScriptRules:
    """Test TypeScript-specific rules"""

    def test_typescript_includes_js_rules(self):
        """Test that TypeScript rules include JavaScript rules"""
        js_rules = ReviewRules.get_javascript_rules()
        ts_rules = ReviewRules.get_typescript_rules()

        # TypeScript should have more rules than JavaScript
        assert len(ts_rules) >= len(js_rules)

    def test_any_type_detection(self):
        """Test 'any' type usage detection"""
        rules = ReviewRules.get_typescript_rules()
        any_rule = next(r for r in rules if r["name"] == "any_type")

        # Should trigger
        assert any_rule["condition"]("function test(x: any)", "function test(x: any)", 1)
        assert any_rule["condition"]("const list: Array<any>", "const list: Array<any>", 1)


class TestReactRules:
    """Test React-specific rules"""

    def test_react_includes_js_rules(self):
        """Test that React rules include JavaScript rules"""
        js_rules = ReviewRules.get_javascript_rules()
        react_rules = ReviewRules.get_react_rules()

        # React should have more rules than JavaScript
        assert len(react_rules) >= len(js_rules)

    def test_missing_key_prop_detection(self):
        """Test missing key prop in React list detection"""
        rules = ReviewRules.get_react_rules()
        key_rule = next(r for r in rules if r["name"] == "missing_key_prop")

        # Should trigger
        test_line = "items.map(item => <div>{item}</div>)"
        assert key_rule["condition"](test_line, test_line.strip(), 1)

        # Should not trigger (has key)
        safe_line = "items.map(item => <div key={item.id}>{item}</div>)"
        assert not key_rule["condition"](safe_line, safe_line.strip(), 1)


class TestRuleSeverityLevels:
    """Test that rules have appropriate severity levels"""

    def test_critical_severity_rules(self):
        """Test that security vulnerabilities are marked as critical"""
        rules = ReviewRules.get_python_rules()

        critical_rules = [
            "subprocess_shell_injection",
            "hardcoded_secrets",
            "sql_injection_risk",
            "eval_usage",
            "exec_usage",
        ]

        for rule_name in critical_rules:
            rule = next(r for r in rules if r["name"] == rule_name)
            result = rule["action"]("test", "test", 1, "test.py")
            assert result["severity"] == "critical", f"{rule_name} should be marked as critical"

    def test_medium_severity_rules(self):
        """Test that code quality issues are marked as medium"""
        rules = ReviewRules.get_python_rules()

        medium_rule = next(r for r in rules if r["name"] == "bare_except")
        result = medium_rule["action"]("except:", "except:", 1, "test.py")
        assert result["severity"] == "medium"

    def test_low_severity_rules(self):
        """Test that style issues are marked as low"""
        rules = ReviewRules.get_python_rules()

        low_rule = next(r for r in rules if r["name"] == "print_statements")
        result = low_rule["action"]('print("test")', 'print("test")', 1, "test.py")
        assert result["severity"] == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
