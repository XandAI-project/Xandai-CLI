"""
Calculator Tool - Perform mathematical calculations
"""

import math
import re


class CalculatorTool:
    """Perform mathematical calculations and operations."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "calculator_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Perform mathematical calculations, evaluate expressions, and solve math problems"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "expression": "string (required) - Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(45)')",
        }

    def execute(self, expression: str):
        """
        Execute the calculation.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Dictionary with calculation result
        """
        try:
            # Clean the expression
            expression = expression.strip()

            # Replace common math functions
            safe_expression = expression.lower()
            safe_expression = safe_expression.replace("^", "**")  # Power operator
            safe_expression = safe_expression.replace("×", "*")
            safe_expression = safe_expression.replace("÷", "/")

            # Create safe namespace with math functions
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "ceil": math.ceil,
                "floor": math.floor,
                "factorial": math.factorial,
            }

            # Evaluate the expression
            result = eval(safe_expression, {"__builtins__": {}}, safe_dict)

            return {
                "success": True,
                "expression": expression,
                "result": result,
                "result_type": type(result).__name__,
            }

        except ZeroDivisionError:
            return {
                "success": False,
                "expression": expression,
                "error": "Division by zero",
            }
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": f"Calculation error: {str(e)}",
            }
