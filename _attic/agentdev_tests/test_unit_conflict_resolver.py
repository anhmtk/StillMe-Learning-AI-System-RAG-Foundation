#!/usr/bin/env python3
"""
Unit tests for Conflict Resolver Module
Tests conflict detection and resolution capabilities
"""

import os
import shutil
import tempfile

import pytest

# Import AgentDev modules
from agent_dev.core.conflict_resolver import (
    ConflictResolver,
    ConflictType,
    ResolutionStrategy,
)


class TestConflictResolver:
    """Test cases for Conflict Resolver Module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.conflict_resolver = ConflictResolver()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_conflict_resolver_initialization(self):
        """Test ConflictResolver initialization"""
        assert self.conflict_resolver is not None
        assert hasattr(self.conflict_resolver, "detect_conflicts")
        assert hasattr(self.conflict_resolver, "resolve_conflicts")
        assert hasattr(self.conflict_resolver, "analyze_import_conflicts")
        assert hasattr(self.conflict_resolver, "analyze_code_conflicts")

    @pytest.mark.unit
    def test_import_conflict_detection(self):
        """Test import conflict detection"""
        # Create files with import conflicts
        file1_path = os.path.join(self.temp_dir, "module1.py")
        file2_path = os.path.join(self.temp_dir, "module2.py")

        with open(file1_path, "w") as f:
            f.write("""
import requests
import numpy as np
import pandas as pd
from typing import List, Dict
""")

        with open(file2_path, "w") as f:
            f.write("""
import requests
import numpy as np
import pandas as pd
from typing import List, Dict
import os
import sys
""")

        # Detect import conflicts
        conflicts = self.conflict_resolver.detect_conflicts(self.temp_dir)

        assert isinstance(conflicts, list)
        assert len(conflicts) > 0

        # Should detect import conflicts
        import_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.IMPORT_CONFLICT
        ]
        assert len(import_conflicts) > 0

    @pytest.mark.unit
    def test_code_conflict_detection(self):
        """Test code conflict detection"""
        # Create files with code conflicts
        file1_path = os.path.join(self.temp_dir, "function1.py")
        file2_path = os.path.join(self.temp_dir, "function2.py")

        with open(file1_path, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
""")

        with open(file2_path, "w") as f:
            f.write("""
def calculate_sum(a, b):
    return a + b + 1  # Different implementation

def calculate_product(a, b):
    return a * b * 2  # Different implementation
""")

        # Detect code conflicts
        conflicts = self.conflict_resolver.detect_conflicts(self.temp_dir)

        assert isinstance(conflicts, list)
        assert len(conflicts) > 0

        # Should detect code conflicts
        code_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.CODE_CONFLICT
        ]
        assert len(code_conflicts) > 0

    @pytest.mark.unit
    def test_merge_conflict_detection(self):
        """Test merge conflict detection"""
        # Create file with merge conflict markers
        conflict_file = os.path.join(self.temp_dir, "conflict.py")
        with open(conflict_file, "w") as f:
            f.write("""
def calculate_sum(a, b):
<<<<<<< HEAD
    return a + b
=======
    return a + b + 1
>>>>>>> branch
""")

        # Detect merge conflicts
        conflicts = self.conflict_resolver.detect_conflicts(self.temp_dir)

        assert isinstance(conflicts, list)
        assert len(conflicts) > 0

        # Should detect merge conflicts
        merge_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.MERGE_CONFLICT
        ]
        assert len(merge_conflicts) > 0

    @pytest.mark.unit
    def test_dependency_conflict_detection(self):
        """Test dependency conflict detection"""
        # Create requirements files with conflicting versions
        req1_path = os.path.join(self.temp_dir, "requirements1.txt")
        req2_path = os.path.join(self.temp_dir, "requirements2.txt")

        with open(req1_path, "w") as f:
            f.write("""
requests==2.25.1
numpy==1.19.5
pandas==1.2.4
""")

        with open(req2_path, "w") as f:
            f.write("""
requests==2.28.0
numpy==1.21.0
pandas==1.4.0
""")

        # Detect dependency conflicts
        conflicts = self.conflict_resolver.detect_conflicts(self.temp_dir)

        assert isinstance(conflicts, list)
        assert len(conflicts) > 0

        # Should detect dependency conflicts
        dep_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.DEPENDENCY_CONFLICT
        ]
        assert len(dep_conflicts) > 0

    @pytest.mark.unit
    def test_conflict_resolution_strategies(self):
        """Test conflict resolution strategies"""
        # Create test conflicts
        conflicts = [
            {
                "type": ConflictType.IMPORT_CONFLICT,
                "file": "module.py",
                "description": "Duplicate import statements",
            },
            {
                "type": ConflictType.CODE_CONFLICT,
                "file": "function.py",
                "description": "Different function implementations",
            },
        ]

        # Test resolution strategies
        for conflict in conflicts:
            resolution = self.conflict_resolver.resolve_conflicts([conflict])

            assert isinstance(resolution, list)
            assert len(resolution) > 0

            # Should provide resolution strategy
            for res in resolution:
                assert "strategy" in res
                assert "confidence" in res
                assert "description" in res
                assert res["strategy"] in [
                    ResolutionStrategy.AUTO_RESOLVE,
                    ResolutionStrategy.MANUAL_REVIEW,
                    ResolutionStrategy.REJECT,
                ]

    @pytest.mark.unit
    def test_auto_resolution_capabilities(self):
        """Test auto-resolution capabilities"""
        # Create simple conflicts that can be auto-resolved
        simple_conflicts = [
            {
                "type": ConflictType.IMPORT_CONFLICT,
                "file": "module.py",
                "description": "Duplicate import statements",
                "severity": "low",
            }
        ]

        resolution = self.conflict_resolver.resolve_conflicts(simple_conflicts)

        # Should suggest auto-resolution for simple conflicts
        auto_resolve = [
            r for r in resolution if r["strategy"] == ResolutionStrategy.AUTO_RESOLVE
        ]
        assert len(auto_resolve) > 0

    @pytest.mark.unit
    def test_manual_review_requirements(self):
        """Test manual review requirements"""
        # Create complex conflicts that require manual review
        complex_conflicts = [
            {
                "type": ConflictType.CODE_CONFLICT,
                "file": "critical_function.py",
                "description": "Different implementations of critical business logic",
                "severity": "high",
            }
        ]

        resolution = self.conflict_resolver.resolve_conflicts(complex_conflicts)

        # Should suggest manual review for complex conflicts
        manual_review = [
            r for r in resolution if r["strategy"] == ResolutionStrategy.MANUAL_REVIEW
        ]
        assert len(manual_review) > 0

    @pytest.mark.unit
    def test_conflict_priority_assessment(self):
        """Test conflict priority assessment"""
        # Create conflicts with different priorities
        conflicts = [
            {
                "type": ConflictType.IMPORT_CONFLICT,
                "file": "utils.py",
                "description": "Duplicate imports",
                "severity": "low",
            },
            {
                "type": ConflictType.CODE_CONFLICT,
                "file": "auth.py",
                "description": "Authentication logic conflict",
                "severity": "high",
            },
        ]

        resolution = self.conflict_resolver.resolve_conflicts(conflicts)

        # Should prioritize high-severity conflicts
        high_priority = [r for r in resolution if r.get("priority", 0) > 0.7]
        assert len(high_priority) > 0

    @pytest.mark.unit
    def test_conflict_resolution_plan(self):
        """Test conflict resolution plan generation"""
        # Create multiple conflicts
        conflicts = [
            {
                "type": ConflictType.IMPORT_CONFLICT,
                "file": "module1.py",
                "description": "Import conflict",
            },
            {
                "type": ConflictType.CODE_CONFLICT,
                "file": "module2.py",
                "description": "Code conflict",
            },
        ]

        resolution_plan = self.conflict_resolver.generate_resolution_plan(conflicts)

        assert isinstance(resolution_plan, dict)
        assert "conflicts" in resolution_plan
        assert "resolution_order" in resolution_plan
        assert "estimated_time" in resolution_plan
        assert "risk_assessment" in resolution_plan

        # Should provide resolution order
        assert len(resolution_plan["resolution_order"]) > 0
        assert resolution_plan["estimated_time"] > 0

    @pytest.mark.unit
    def test_conflict_resolver_performance(self):
        """Test conflict resolver performance"""
        import time

        # Create large number of files with conflicts
        for i in range(100):
            file_path = os.path.join(self.temp_dir, f"module_{i}.py")
            with open(file_path, "w") as f:
                f.write(f"""
import requests
import numpy as np
import pandas as pd

def function_{i}():
    return {i}
""")

        start_time = time.time()
        conflicts = self.conflict_resolver.detect_conflicts(self.temp_dir)
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 3.0  # Less than 3 seconds
        assert len(conflicts) > 0

    @pytest.mark.unit
    def test_empty_directory_handling(self):
        """Test handling of empty directory"""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)

        conflicts = self.conflict_resolver.detect_conflicts(empty_dir)

        # Should handle empty directory gracefully
        assert isinstance(conflicts, list)
        assert len(conflicts) == 0

    @pytest.mark.unit
    def test_conflict_resolver_deterministic(self):
        """Test that conflict resolver is deterministic"""
        # Create test files
        file1_path = os.path.join(self.temp_dir, "test1.py")
        file2_path = os.path.join(self.temp_dir, "test2.py")

        with open(file1_path, "w") as f:
            f.write("import requests\nimport numpy")

        with open(file2_path, "w") as f:
            f.write("import requests\nimport numpy")

        # Run detection multiple times
        result1 = self.conflict_resolver.detect_conflicts(self.temp_dir)
        result2 = self.conflict_resolver.detect_conflicts(self.temp_dir)

        # Results should be identical
        assert len(result1) == len(result2)
        for item1, item2 in zip(result1, result2, strict=False):
            assert item1.conflict_type == item2.conflict_type
            assert item1.description == item2.description

    @pytest.mark.unit
    def test_conflict_resolver_edge_cases(self):
        """Test edge cases for conflict resolver"""
        # Test with non-existent directory
        with pytest.raises((FileNotFoundError, OSError)):
            self.conflict_resolver.detect_conflicts("/non/existent/path")

        # Test with file instead of directory
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        with pytest.raises((NotADirectoryError, OSError)):
            self.conflict_resolver.detect_conflicts(test_file)

    @pytest.mark.unit
    def test_conflict_resolution_confidence(self):
        """Test conflict resolution confidence scoring"""
        # Create conflicts with different complexity levels
        simple_conflict = {
            "type": ConflictType.IMPORT_CONFLICT,
            "file": "simple.py",
            "description": "Duplicate import",
            "complexity": "low",
        }

        complex_conflict = {
            "type": ConflictType.CODE_CONFLICT,
            "file": "complex.py",
            "description": "Complex business logic conflict",
            "complexity": "high",
        }

        # Test resolution confidence
        simple_resolution = self.conflict_resolver.resolve_conflicts([simple_conflict])
        complex_resolution = self.conflict_resolver.resolve_conflicts(
            [complex_conflict]
        )

        # Simple conflicts should have higher confidence
        simple_confidence = simple_resolution[0]["confidence"]
        complex_confidence = complex_resolution[0]["confidence"]

        assert simple_confidence > complex_confidence


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
