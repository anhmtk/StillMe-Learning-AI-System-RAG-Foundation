#!/usr/bin/env python3
"""
Simple Calculator - Test Repository for AgentDev
Contains intentional bugs for testing auto-fix capabilities
"""

import sys
from typing import Union

class Calculator:
    """Simple calculator with intentional bugs"""
    
    def __init__(self):
        self.history = []
        self.memory = 0
    
    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Add two numbers - has off-by-one error"""
        result = a + b + 1  # BUG: off-by-one error
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Subtract two numbers"""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Multiply two numbers - has division by zero potential"""
        if b == 0:
            raise ValueError("Cannot multiply by zero")  # BUG: should be "Cannot multiply by zero"
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Divide two numbers - has division by zero bug"""
        if b == 0:
            return float('inf')  # BUG: should raise ValueError
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base: Union[int, float], exponent: Union[int, float]) -> Union[int, float]:
        """Calculate power - has performance issue"""
        # BUG: Inefficient implementation for large exponents
        result = 1
        for _ in range(int(exponent)):  # BUG: Should use ** operator
            result *= base
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    def factorial(self, n: int) -> int:
        """Calculate factorial - has negative number bug"""
        if n < 0:
            return -1  # BUG: should raise ValueError
        if n == 0:
            return 1
        result = 1
        for i in range(1, n + 1):
            result *= i
        self.history.append(f"{n}! = {result}")
        return result
    
    def get_history(self) -> list[str]:
        """Get calculation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()
    
    def store_memory(self, value: Union[int, float]):
        """Store value in memory"""
        self.memory = value
    
    def recall_memory(self) -> Union[int, float]:
        """Recall value from memory"""
        return self.memory
    
    def clear_memory(self):
        """Clear memory"""
        self.memory = 0

def main():
    """Main function with potential issues"""
    calc = Calculator()
    
    # Test cases that will trigger bugs
    try:
        print("Testing calculator...")
        
        # This will trigger off-by-one error
        result = calc.add(5, 3)
        print(f"5 + 3 = {result}")  # Should be 8, but will be 9
        
        # This will trigger division by zero
        result = calc.divide(10, 0)
        print(f"10 / 0 = {result}")  # Should raise error, but returns inf
        
        # This will trigger negative factorial
        result = calc.factorial(-5)
        print(f"(-5)! = {result}")  # Should raise error, but returns -1
        
        # This will be slow due to inefficient power
        result = calc.power(2, 1000)
        print(f"2^1000 = {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
