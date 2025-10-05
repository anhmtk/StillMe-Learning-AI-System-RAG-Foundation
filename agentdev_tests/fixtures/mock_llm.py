#!/usr/bin/env python3
"""
Mock LLM Provider for AgentDev Testing
Provides deterministic responses for testing consistency
"""

import hashlib
import random
from dataclasses import dataclass
from typing import Any


@dataclass
class MockLLMResponse:
    """Mock LLM response structure"""

    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str
    response_time: float


class MockLLMProvider:
    """Mock LLM provider with deterministic behavior"""

    def __init__(self, seed: int = 42):
        """Initialize mock LLM with seed for deterministic behavior"""
        self.seed = seed
        self.random = random.Random(seed)
        self.call_count = 0
        self.responses = []
        self.models = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "claude-3-opus"]

    def generate_response(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> MockLLMResponse:
        """Generate deterministic mock response"""
        self.call_count += 1

        # Create deterministic hash from prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        hash_int = int(prompt_hash[:8], 16)

        # Use hash to generate deterministic response
        self.random.seed(self.seed + hash_int + self.call_count)

        # Generate response based on prompt content
        response_content = self._generate_content(prompt, model)

        # Calculate usage metrics
        input_tokens = len(prompt.split())
        output_tokens = len(response_content.split())

        response = MockLLMResponse(
            content=response_content,
            model=model,
            usage={
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            finish_reason="stop",
            response_time=self.random.uniform(0.1, 2.0),
        )

        self.responses.append(response)
        return response

    def _generate_content(self, prompt: str, model: str) -> str:
        """Generate content based on prompt analysis"""
        prompt_lower = prompt.lower()

        # Code generation prompts
        if "generate code" in prompt_lower or "write function" in prompt_lower:
            return self._generate_code_response(prompt)

        # Bug fixing prompts
        elif "fix bug" in prompt_lower or "error" in prompt_lower:
            return self._generate_bug_fix_response(prompt)

        # Analysis prompts
        elif "analyze" in prompt_lower or "review" in prompt_lower:
            return self._generate_analysis_response(prompt)

        # Security prompts
        elif "security" in prompt_lower or "vulnerability" in prompt_lower:
            return self._generate_security_response(prompt)

        # Performance prompts
        elif "performance" in prompt_lower or "optimize" in prompt_lower:
            return self._generate_performance_response(prompt)

        # Default response
        else:
            return self._generate_default_response(prompt)

    def _generate_code_response(self, prompt: str) -> str:
        """Generate code response"""
        if "calculator" in prompt.lower():
            return '''def add(a, b):
    """Add two numbers"""
    return a + b

def subtract(a, b):
    """Subtract two numbers"""
    return a - b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b

def divide(a, b):
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b'''

        elif "data processor" in prompt.lower():
            return '''def process_data_efficiently(data):
    """Process data with O(n) complexity"""
    processed = []
    seen_ids = set()
    
    for item in data:
        if item.get('id') not in seen_ids:
            processed.append(item)
            seen_ids.add(item['id'])
    
    return processed'''

        else:
            return "# Generated code based on requirements\n# Implementation follows best practices"

    def _generate_bug_fix_response(self, prompt: str) -> str:
        """Generate bug fix response"""
        if "off-by-one" in prompt.lower():
            return """# Fix: Remove the +1 that causes off-by-one error
def add(a, b):
    return a + b  # Fixed: removed +1"""

        elif "division by zero" in prompt.lower():
            return """# Fix: Add proper error handling
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b"""

        elif "performance" in prompt.lower():
            return """# Fix: Use efficient algorithm
def power(base, exponent):
    return base ** exponent  # Much faster than loop"""

        else:
            return "# Bug fix applied\n# Code now handles edge cases properly"

    def _generate_analysis_response(self, prompt: str) -> str:
        """Generate analysis response"""
        return """## Analysis Results

**Impact Assessment:**
- High impact on user experience
- Affects multiple components
- Requires immediate attention

**Security Implications:**
- No security vulnerabilities detected
- Follows secure coding practices

**Performance Impact:**
- Minimal performance overhead
- Efficient algorithm implementation

**Recommendations:**
1. Implement proper error handling
2. Add comprehensive tests
3. Update documentation"""

    def _generate_security_response(self, prompt: str) -> str:
        """Generate security response"""
        return """## Security Analysis

**Vulnerability Assessment:**
- No critical vulnerabilities found
- Input validation implemented
- Secure coding practices followed

**Risk Level:** LOW

**Security Recommendations:**
1. Implement input sanitization
2. Add authentication checks
3. Use secure communication protocols
4. Regular security audits

**Compliance:**
- OWASP guidelines followed
- Industry standards met"""

    def _generate_performance_response(self, prompt: str) -> str:
        """Generate performance response"""
        return """## Performance Analysis

**Current Performance:**
- Time Complexity: O(n²) - needs optimization
- Memory Usage: High - can be reduced
- Response Time: Slow - requires improvement

**Optimization Recommendations:**
1. Use efficient algorithms (O(n) instead of O(n²))
2. Implement caching mechanisms
3. Reduce memory allocations
4. Use async operations where possible

**Expected Improvements:**
- 50% faster execution
- 30% less memory usage
- Better scalability"""

    def _generate_default_response(self, prompt: str) -> str:
        """Generate default response"""
        return f"Mock response for: {prompt[:100]}..."

    def get_call_statistics(self) -> dict[str, Any]:
        """Get call statistics"""
        if not self.responses:
            return {"total_calls": 0, "avg_response_time": 0}

        total_time = sum(r.response_time for r in self.responses)
        avg_time = total_time / len(self.responses)

        return {
            "total_calls": self.call_count,
            "avg_response_time": avg_time,
            "total_tokens": sum(r.usage["total_tokens"] for r in self.responses),
            "models_used": list(set(r.model for r in self.responses)),
        }

    def reset(self):
        """Reset mock LLM state"""
        self.call_count = 0
        self.responses.clear()
        self.random = random.Random(self.seed)

    def set_seed(self, seed: int):
        """Set new seed for deterministic behavior"""
        self.seed = seed
        self.random = random.Random(seed)


# Global mock LLM instance for testing
mock_llm = MockLLMProvider(seed=42)
