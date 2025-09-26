# Calculator Plugin

A simple calculator plugin for the StillMe AI Framework demonstrating the plugin architecture.

## Features

- Basic arithmetic operations (+, -, *, /)
- Parentheses support
- Expression validation
- Error handling
- Configurable precision

## Usage

```python
from plugins.calculator import CalculatorPlugin

# Create plugin instance
calc = CalculatorPlugin()

# Initialize
await calc.initialize()

# Calculate expressions
result = await calc.process("2 + 3")
# Returns: {"success": True, "expression": "2 + 3", "result": 5.0}

# Cleanup
await calc.cleanup()
```

## Configuration

```python
config = {
    "max_expression_length": 100,
    "precision": 10
}

calc = CalculatorPlugin(config)
```

## Examples

- `"2 + 3"` → `5.0`
- `"(10 - 2) * 3"` → `24.0`
- `"15 / 3"` → `5.0`
- `"2 * (3 + 4)"` → `14.0`

## Error Handling

The plugin validates expressions and returns detailed error messages for:
- Invalid characters
- Unbalanced parentheses
- Division by zero
- Consecutive operators
- Expression too long

## Testing

Run the plugin directly to test:

```bash
python plugins/calculator/calculator_plugin.py
```
