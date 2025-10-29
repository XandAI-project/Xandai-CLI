"""
JSON Formatter Tool - Format, validate, and minify JSON
"""

import json


class JsonFormatterTool:
    """Format, validate, minify, and manipulate JSON data."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "json_formatter_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Format, validate, minify JSON data, or convert between JSON and Python dict"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "json_string": "string (required) - JSON string to process",
            "operation": "string (optional) - Operation: 'format', 'minify', 'validate' (default: 'format')",
            "indent": "integer (optional) - Indentation level for formatting (default: 2)",
        }

    def execute(self, json_string: str, operation: str = "format", indent: int = 2):
        """
        Execute the JSON operation.

        Args:
            json_string: JSON string to process
            operation: Operation to perform
            indent: Indentation level for formatting

        Returns:
            Dictionary with operation results
        """
        try:
            operation = operation.lower()

            # Parse JSON
            try:
                data = json.loads(json_string)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "valid": False,
                    "error": f"Invalid JSON: {str(e)}",
                    "error_line": e.lineno if hasattr(e, "lineno") else None,
                    "error_column": e.colno if hasattr(e, "colno") else None,
                }

            # Perform operation
            if operation == "validate":
                return {
                    "success": True,
                    "valid": True,
                    "message": "JSON is valid",
                    "type": self._get_json_type(data),
                    "size": self._get_data_size(data),
                }

            elif operation == "format":
                formatted = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=False)
                return {
                    "success": True,
                    "valid": True,
                    "operation": "format",
                    "result": formatted,
                    "original_size": len(json_string),
                    "formatted_size": len(formatted),
                    "type": self._get_json_type(data),
                }

            elif operation == "minify":
                minified = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
                return {
                    "success": True,
                    "valid": True,
                    "operation": "minify",
                    "result": minified,
                    "original_size": len(json_string),
                    "minified_size": len(minified),
                    "compression_ratio": f"{(1 - len(minified) / len(json_string)) * 100:.1f}%",
                    "type": self._get_json_type(data),
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Use: format, minify, validate",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
            }

    @staticmethod
    def _get_json_type(data):
        """Get the type of JSON data."""
        if isinstance(data, dict):
            return f"object with {len(data)} keys"
        elif isinstance(data, list):
            return f"array with {len(data)} items"
        elif isinstance(data, str):
            return "string"
        elif isinstance(data, (int, float)):
            return "number"
        elif isinstance(data, bool):
            return "boolean"
        elif data is None:
            return "null"
        return "unknown"

    @staticmethod
    def _get_data_size(data):
        """Get approximate size information about the data."""
        if isinstance(data, dict):
            return {
                "keys": len(data),
                "nested_objects": sum(1 for v in data.values() if isinstance(v, dict)),
                "nested_arrays": sum(1 for v in data.values() if isinstance(v, list)),
            }
        elif isinstance(data, list):
            return {
                "items": len(data),
                "nested_objects": sum(1 for v in data if isinstance(v, dict)),
                "nested_arrays": sum(1 for v in data if isinstance(v, list)),
            }
        return None
