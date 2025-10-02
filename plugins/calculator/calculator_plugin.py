"""
Calculator Plugin for StillMe AI Framework
==========================================

A simple calculator plugin demonstrating the plugin architecture.
"""

import logging
import re
from typing import Any, Optional

from stillme_core.base.module_base import ModuleBase, ModuleInfo, ModuleStatus

logger = logging.getLogger(__name__)


class CalculatorPlugin(ModuleBase):
    """
    Calculator plugin for basic mathematical operations

    Supports:
    - Basic arithmetic (+, -, *, /)
    - Parentheses
    - Simple expressions
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        self.supported_operations = ["+", "-", "*", "/", "(", ")"]
        self.max_expression_length = self.config.get("max_expression_length", 100)
        self.precision = self.config.get("precision", 10)

    @property
    def module_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="CalculatorPlugin",
            version="1.0.0",
            description="Basic calculator with arithmetic operations",
            author="StillMe Framework Team",
            status=self._status,
            dependencies=["re"],
            config_schema={
                "max_expression_length": {"type": "int", "default": 100},
                "precision": {"type": "int", "default": 10},
            },
        )

    async def initialize(self) -> bool:
        """Initialize the calculator plugin"""
        try:
            logger.info("Initializing Calculator Plugin")
            self._set_status(ModuleStatus.RUNNING)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Calculator Plugin: {e}")
            self._set_status(ModuleStatus.ERROR)
            return False

    async def process(self, input_data: Any) -> Any:
        """Process calculator input"""
        try:
            if isinstance(input_data, str):
                expression = input_data.strip()
            elif isinstance(input_data, dict) and "expression" in input_data:
                expression = input_data["expression"].strip()
            else:
                return {
                    "error": "Invalid input format",
                    "expected": "string or dict with 'expression' key",
                }

            # Validate expression
            validation_result = self._validate_expression(expression)
            if not validation_result["valid"]:
                return {
                    "error": "Invalid expression",
                    "details": validation_result["errors"],
                }

            # Calculate result
            result = self._calculate(expression)

            return {
                "success": True,
                "expression": expression,
                "result": result,
                "formatted_result": f"{expression} = {result}",
            }

        except Exception as e:
            logger.error(f"Calculator processing error: {e}")
            return {"error": "Calculation failed", "details": str(e)}

    async def cleanup(self) -> None:
        """Cleanup calculator plugin"""
        logger.info("Cleaning up Calculator Plugin")
        self._set_status(ModuleStatus.STOPPED)

    def _validate_expression(self, expression: str) -> dict[str, Any]:
        """Validate mathematical expression"""
        errors = []

        # Check length
        if len(expression) > self.max_expression_length:
            errors.append(
                f"Expression too long (max {self.max_expression_length} characters)"
            )

        # Check for empty expression
        if not expression:
            errors.append("Empty expression")
            return {"valid": False, "errors": errors}

        # Check for valid characters
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            errors.append("Expression contains invalid characters")

        # Check for balanced parentheses
        if not self._check_balanced_parentheses(expression):
            errors.append("Unbalanced parentheses")

        # Check for division by zero (basic check)
        if "/0" in expression.replace(" ", ""):
            errors.append("Division by zero detected")

        # Check for consecutive operators
        if re.search(r"[+\-*/]{2,}", expression):
            errors.append("Consecutive operators not allowed")

        return {"valid": len(errors) == 0, "errors": errors}

    def _check_balanced_parentheses(self, expression: str) -> bool:
        """Check if parentheses are balanced"""
        count = 0
        for char in expression:
            if char == "(":
                count += 1
            elif char == ")":
                count -= 1
                if count < 0:
                    return False
        return count == 0

    def _calculate(self, expression: str) -> float:
        """Calculate mathematical expression"""
        try:
            # Clean expression
            clean_expression = expression.replace(" ", "")

            # Handle simple cases first
            if clean_expression.isdigit():
                return float(clean_expression)

            # Use eval for simple expressions (in production, use a proper parser)
            # This is a simplified implementation for demonstration
            result = eval(clean_expression)

            # Round to specified precision
            return round(float(result), self.precision)

        except ZeroDivisionError:
            raise ValueError("Division by zero")
        except SyntaxError:
            raise ValueError("Invalid expression syntax")
        except Exception as e:
            raise ValueError(f"Calculation error: {str(e)}")

    def get_supported_operations(self) -> list:
        """Get list of supported operations"""
        return self.supported_operations.copy()

    def get_help(self) -> str:
        """Get help information"""
        return f"""
Calculator Plugin Help:
=====================

Supported operations:
- Addition: +
- Subtraction: -
- Multiplication: *
- Division: /
- Parentheses: ( )

Examples:
- "2 + 3" → 5
- "(10 - 2) * 3" → 24
- "15 / 3" → 5

Limitations:
- Maximum expression length: {self.max_expression_length} characters
- Precision: {self.precision} decimal places
- No advanced functions (sin, cos, etc.)

Usage:
- Pass expression as string: "2 + 3"
- Or as dict: {{"expression": "2 + 3"}}
        """


# Plugin factory function
def create_plugin(config: Optional[dict[str, Any]] = None) -> CalculatorPlugin:
    """Create calculator plugin instance"""
    return CalculatorPlugin(config)


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_calculator():
        calc = CalculatorPlugin()
        await calc.initialize()

        # Test expressions
        test_expressions = [
            "2 + 3",
            "(10 - 2) * 3",
            "15 / 3",
            "2 * (3 + 4)",
            "invalid expression",
        ]

        for expr in test_expressions:
            result = await calc.process(expr)
            print(f"Input: {expr}")
            print(f"Output: {result}")
            print("-" * 40)

        await calc.cleanup()

    asyncio.run(test_calculator())
