"""
Tests for Template Manager
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from xandai.templates.template_manager import (
    Template,
    TemplateManager,
    TemplateParameter,
    render_template,
)


class TestTemplate:
    """Test Template class"""

    def test_template_render_simple(self):
        """Test simple template rendering"""
        template = Template(
            name="test",
            description="Test template",
            version="1.0",
            category="test",
            parameters=[TemplateParameter(name="name", type="string", required=True)],
            template="Hello {name}!",
        )

        result = template.render(name="World")
        assert result == "Hello World!"

    def test_template_render_with_default(self):
        """Test rendering with default parameter"""
        template = Template(
            name="test",
            description="Test",
            version="1.0",
            category="test",
            parameters=[
                TemplateParameter(name="greeting", type="string", required=False, default="Hi")
            ],
            template="{greeting}!",
        )

        result = template.render()
        assert result == "Hi!"

    def test_template_missing_required_param(self):
        """Test error on missing required parameter"""
        template = Template(
            name="test",
            description="Test",
            version="1.0",
            category="test",
            parameters=[TemplateParameter(name="required_param", type="string", required=True)],
            template="{required_param}",
        )

        with pytest.raises(ValueError, match="Required parameter"):
            template.render()


class TestTemplateManager:
    """Test TemplateManager class"""

    def test_add_custom_template(self):
        """Test adding custom template"""
        manager = TemplateManager()

        template = Template(
            name="custom",
            description="Custom template",
            version="1.0",
            category="custom",
            parameters=[],
            template="Custom content",
        )

        manager.add_custom_template(template)
        assert "custom" in manager.list_templates()

    def test_load_template(self):
        """Test loading template"""
        manager = TemplateManager()

        # Add a template
        template = Template(
            name="test_load",
            description="Test",
            version="1.0",
            category="test",
            parameters=[],
            template="Test",
        )
        manager.add_custom_template(template)

        loaded = manager.load_template("test_load")
        assert loaded.name == "test_load"

    def test_load_nonexistent_template(self):
        """Test error when loading nonexistent template"""
        manager = TemplateManager()

        with pytest.raises(ValueError, match="Template .* not found"):
            manager.load_template("nonexistent")

    def test_render_template(self):
        """Test rendering template through manager"""
        manager = TemplateManager()

        template = Template(
            name="test_render",
            description="Test",
            version="1.0",
            category="test",
            parameters=[TemplateParameter(name="value", type="string", required=True)],
            template="Value: {value}",
        )
        manager.add_custom_template(template)

        result = manager.render("test_render", value="123")
        assert result == "Value: 123"

    def test_list_templates(self):
        """Test listing all templates"""
        manager = TemplateManager()

        template1 = Template("t1", "Test 1", "1.0", "cat1", [], "t1")
        template2 = Template("t2", "Test 2", "1.0", "cat2", [], "t2")

        manager.add_custom_template(template1)
        manager.add_custom_template(template2)

        templates = manager.list_templates()
        assert "t1" in templates
        assert "t2" in templates

    def test_list_templates_by_category(self):
        """Test filtering templates by category"""
        manager = TemplateManager()

        template1 = Template("t1", "Test 1", "1.0", "cat1", [], "t1")
        template2 = Template("t2", "Test 2", "1.0", "cat1", [], "t2")
        template3 = Template("t3", "Test 3", "1.0", "cat2", [], "t3")

        manager.add_custom_template(template1)
        manager.add_custom_template(template2)
        manager.add_custom_template(template3)

        cat1_templates = manager.list_templates(category="cat1")
        assert "t1" in cat1_templates
        assert "t2" in cat1_templates
        assert "t3" not in cat1_templates

    def test_list_categories(self):
        """Test listing all categories"""
        manager = TemplateManager()

        template1 = Template("t1", "Test 1", "1.0", "category_a", [], "t1")
        template2 = Template("t2", "Test 2", "1.0", "category_b", [], "t2")

        manager.add_custom_template(template1)
        manager.add_custom_template(template2)

        categories = manager.list_categories()
        assert "category_a" in categories
        assert "category_b" in categories

    def test_get_template_info(self):
        """Test getting template information"""
        manager = TemplateManager()

        template = Template(
            name="info_test",
            description="Test info",
            version="2.0",
            category="info",
            parameters=[
                TemplateParameter(
                    name="param1", type="string", required=True, description="First param"
                )
            ],
            template="Test",
        )
        manager.add_custom_template(template)

        info = manager.get_template_info("info_test")

        assert info["name"] == "info_test"
        assert info["description"] == "Test info"
        assert info["version"] == "2.0"
        assert info["category"] == "info"
        assert len(info["parameters"]) == 1
        assert info["parameters"][0]["name"] == "param1"

    def test_load_from_yaml_file(self):
        """Test loading template from YAML file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test YAML template
            template_data = {
                "name": "yaml_test",
                "description": "YAML test template",
                "version": "1.0",
                "category": "test",
                "parameters": [
                    {
                        "name": "param1",
                        "type": "string",
                        "required": True,
                        "description": "Test parameter",
                    }
                ],
                "template": "Hello {param1}!",
            }

            yaml_path = Path(tmpdir) / "test_template.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump(template_data, f)

            # Load template
            manager = TemplateManager(template_dir=tmpdir)

            assert "yaml_test" in manager.list_templates()
            result = manager.render("yaml_test", param1="YAML")
            assert result == "Hello YAML!"


def test_render_template_function():
    """Test convenience render_template function"""
    from xandai.templates.template_manager import get_template_manager

    manager = get_template_manager()
    template = Template(
        name="func_test",
        description="Test",
        version="1.0",
        category="test",
        parameters=[TemplateParameter(name="x", type="string", required=True)],
        template="{x}",
    )
    manager.add_custom_template(template)

    result = render_template("func_test", x="test_value")
    assert result == "test_value"
