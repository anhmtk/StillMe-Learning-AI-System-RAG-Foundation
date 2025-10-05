import unittest
from unittest import defaultTestLoader

suite = defaultTestLoader.discover("test_app")
runner = unittest.TextTestRunner()
result = runner.run(suite)
print(f"Result: {result!s}")
