#!/usr/bin/env python3
"""
Test cases for Simple Calculator
These tests will fail due to intentional bugs in main.py
"""

import unittest
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import Calculator

class TestCalculator(unittest.TestCase):
    """Test cases for Calculator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calc = Calculator()
    
    def test_add(self):
        """Test addition - should fail due to off-by-one bug"""
        result = self.calc.add(5, 3)
        self.assertEqual(result, 8)  # This will fail (actual: 9)
    
    def test_subtract(self):
        """Test subtraction"""
        result = self.calc.subtract(10, 4)
        self.assertEqual(result, 6)
    
    def test_multiply(self):
        """Test multiplication"""
        result = self.calc.multiply(3, 4)
        self.assertEqual(result, 12)
    
    def test_divide(self):
        """Test division"""
        result = self.calc.divide(15, 3)
        self.assertEqual(result, 5)
    
    def test_divide_by_zero(self):
        """Test division by zero - should raise ValueError"""
        with self.assertRaises(ValueError):
            self.calc.divide(10, 0)
    
    def test_power(self):
        """Test power calculation"""
        result = self.calc.power(2, 3)
        self.assertEqual(result, 8)
    
    def test_factorial(self):
        """Test factorial calculation"""
        result = self.calc.factorial(5)
        self.assertEqual(result, 120)
    
    def test_factorial_zero(self):
        """Test factorial of zero"""
        result = self.calc.factorial(0)
        self.assertEqual(result, 1)
    
    def test_factorial_negative(self):
        """Test factorial of negative number - should raise ValueError"""
        with self.assertRaises(ValueError):
            self.calc.factorial(-5)
    
    def test_history(self):
        """Test calculation history"""
        self.calc.clear_history()
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        
        history = self.calc.get_history()
        self.assertEqual(len(history), 2)
        self.assertIn("1 + 2 = 3", history)  # This will fail due to off-by-one
        self.assertIn("5 - 3 = 2", history)
    
    def test_memory(self):
        """Test memory operations"""
        self.calc.store_memory(42)
        self.assertEqual(self.calc.recall_memory(), 42)
        
        self.calc.clear_memory()
        self.assertEqual(self.calc.recall_memory(), 0)

if __name__ == "__main__":
    unittest.main()
