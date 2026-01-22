"""
Template Manager

Manages reusable prompt templates for AI operations.
Supports YAML-based templates with variable substitution.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TemplateParameter:
    """Template parameter definition"""

    name: str
    type: str
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass
class Template:
    """Prompt template"""

    name: str
    description: str
    version: str
    category: str
    parameters: List[TemplateParameter]
    template: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs) -> str:
        """
        Render template with provided parameters

        Args:
            **kwargs: Parameter values

        Returns:
            Rendered template string
        """
        # Validate required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                if param.default is not None:
                    kwargs[param.name] = param.default
                else:
                    raise ValueError(f"Required parameter '{param.name}' not provided")

        # Apply defaults for missing optional parameters
        for param in self.parameters:
            if param.name not in kwargs and param.default is not None:
                kwargs[param.name] = param.default

        # Render template
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template rendering failed: missing variable {e}")


class TemplateManager:
    """
    Template Manager

    Loads, manages, and renders prompt templates.
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template manager

        Args:
            template_dir: Directory containing templates
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to templates directory next to this file
            self.template_dir = Path(__file__).parent

        self.templates: Dict[str, Template] = {}
        self._load_templates()

    def load_template(self, name: str) -> Template:
        """
        Load a specific template

        Args:
            name: Template name

        Returns:
            Template object
        """
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")

        return self.templates[name]

    def render(self, name: str, **kwargs) -> str:
        """
        Render a template with parameters

        Args:
            name: Template name
            **kwargs: Parameter values

        Returns:
            Rendered template string
        """
        template = self.load_template(name)
        return template.render(**kwargs)

    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """
        List available templates

        Args:
            category: Optional category filter

        Returns:
            List of template names
        """
        if category:
            return [
                name for name, template in self.templates.items() if template.category == category
            ]
        return sorted(self.templates.keys())

    def list_categories(self) -> List[str]:
        """List all template categories"""
        categories = set(t.category for t in self.templates.values())
        return sorted(categories)

    def get_template_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about a template

        Args:
            name: Template name

        Returns:
            Template metadata
        """
        template = self.load_template(name)
        return {
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "category": template.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "required": p.required,
                    "default": p.default,
                    "description": p.description,
                }
                for p in template.parameters
            ],
        }

    def add_custom_template(self, template: Template):
        """
        Add a custom template programmatically

        Args:
            template: Template object
        """
        self.templates[template.name] = template

    def _load_templates(self):
        """Load all templates from directory"""
        if not self.template_dir.exists():
            return

        # Scan for YAML files recursively
        for yaml_file in self.template_dir.rglob("*.yaml"):
            try:
                template = self._load_template_file(yaml_file)
                if template:
                    self.templates[template.name] = template
            except Exception as e:
                # Skip invalid templates
                if os.getenv("XANDAI_DEBUG"):
                    print(f"Warning: Failed to load template {yaml_file}: {e}")

    def _load_template_file(self, file_path: Path) -> Optional[Template]:
        """Load a single template file"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Parse parameters
        params = []
        for param_data in data.get("parameters", []):
            params.append(
                TemplateParameter(
                    name=param_data["name"],
                    type=param_data.get("type", "string"),
                    required=param_data.get("required", True),
                    default=param_data.get("default"),
                    description=param_data.get("description", ""),
                )
            )

        return Template(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            category=data.get("category", "general"),
            parameters=params,
            template=data["template"],
            metadata=data.get("metadata", {}),
        )


# Global template manager instance
_manager = None


def get_template_manager() -> TemplateManager:
    """Get global template manager instance"""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager


def render_template(name: str, **kwargs) -> str:
    """Convenience function to render a template"""
    manager = get_template_manager()
    return manager.render(name, **kwargs)
