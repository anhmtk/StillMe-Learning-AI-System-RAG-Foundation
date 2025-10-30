"""
Test for BugMemory.record method
"""

import json

from stillme_core.bug_memory import BugMemory


class TestBugMemoryRecord:
    def test_record_basic(self, tmp_path):
        """Test basic record functionality"""
        memory_file = tmp_path / "test_memory.jsonl"
        bug_memory = BugMemory(storage=str(memory_file))

        # Record a bug
        bug_memory.record(
            file="test.py",
            test_name="test_function",
            message="AssertionError: expected 1, got 2",
            line=10,
        )

        # Check if file was created
        assert memory_file.exists()

        # Read and verify content
        with memory_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

            record = json.loads(lines[0])
            assert record["file"] == "test.py"
            assert record["test_name"] == "test_function"
            assert record["message"] == "AssertionError: expected 1, got 2"
            assert record["line"] == 10
            assert "fingerprint" in record
            assert "timestamp" in record

    def test_record_duplicate_prevention(self, tmp_path):
        """Test that duplicate records are prevented"""
        memory_file = tmp_path / "test_memory.jsonl"
        bug_memory = BugMemory(storage=str(memory_file))

        # Record the same bug twice
        bug_memory.record(
            file="test.py",
            test_name="test_function",
            message="AssertionError: expected 1, got 2",
            line=10,
        )

        bug_memory.record(
            file="test.py",
            test_name="test_function",
            message="AssertionError: expected 1, got 2",
            line=10,
        )

        # Should only have one record
        with memory_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

    def test_record_minimal_args(self, tmp_path):
        """Test record with minimal arguments"""
        memory_file = tmp_path / "test_memory.jsonl"
        bug_memory = BugMemory(storage=str(memory_file))

        # Record with minimal args
        bug_memory.record(file="test.py", message="Error occurred")

        # Check if file was created
        assert memory_file.exists()

        # Read and verify content
        with memory_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

            record = json.loads(lines[0])
            assert record["file"] == "test.py"
            assert record["message"] == "Error occurred"
            assert record["test_name"] is None
            assert record["line"] is None

    def test_record_fingerprint_consistency(self, tmp_path):
        """Test that fingerprint is consistent for same inputs"""
        memory_file = tmp_path / "test_memory.jsonl"
        bug_memory = BugMemory(storage=str(memory_file))

        # Record same bug twice with different timestamps
        bug_memory.record(
            file="test.py", test_name="test_function", message="AssertionError", line=10
        )

        # Get the fingerprint from first record
        with memory_file.open("r", encoding="utf-8") as f:
            first_record = json.loads(f.readline())
            first_fingerprint = first_record["fingerprint"]

        # Clear file and record again
        memory_file.unlink()

        bug_memory.record(
            file="test.py", test_name="test_function", message="AssertionError", line=10
        )

        # Get fingerprint from second record
        with memory_file.open("r", encoding="utf-8") as f:
            second_record = json.loads(f.readline())
            second_fingerprint = second_record["fingerprint"]

        # Fingerprints should be the same
        assert first_fingerprint == second_fingerprint
