"""
Test for PatchExecutor.apply_patch_and_test method
"""
import pytest
from pathlib import Path
from stillme_core.executor import PatchExecutor, ExecResult
from stillme_core.plan_types import PlanItem


class TestPatchExecutor:
    def test_apply_patch_and_test_with_patch(self, tmp_path):
        """Test apply_patch_and_test with a valid patch"""
        executor = PatchExecutor(repo_root=str(tmp_path))
        
        # Create a simple test file
        test_file = tmp_path / "test_file.py"
        test_file.write_text("def test_something():\n    assert True\n")
        
        # Create a plan item with patch
        plan_item = PlanItem(
            id="test-1",
            title="Test patch",
            action="edit_file",
            target=str(test_file),
            patch="""--- a/test_file.py
+++ b/test_file.py
@@ -1,2 +1,2 @@
-def test_something():
-    assert True
+def test_something():
+    assert True  # Added comment"""
        )
        
        result = executor.apply_patch_and_test(plan_item)
        
        assert isinstance(result, dict)
        assert "ok" in result
        assert "stdout" in result
        assert "stderr" in result

    def test_apply_patch_and_test_without_patch(self, tmp_path):
        """Test apply_patch_and_test without patch (just run tests)"""
        executor = PatchExecutor(repo_root=str(tmp_path))
        
        # Create a simple test file
        test_file = tmp_path / "test_file.py"
        test_file.write_text("def test_something():\n    assert True\n")
        
        # Create a plan item without patch
        plan_item = PlanItem(
            id="test-2",
            title="Test without patch",
            action="run_tests",
            target=str(test_file),
            tests_to_run=[str(test_file)]
        )
        
        result = executor.apply_patch_and_test(plan_item)
        
        assert isinstance(result, dict)
        assert "ok" in result
        assert "tests_run" in result

    def test_apply_patch_and_test_invalid_patch(self, tmp_path):
        """Test apply_patch_and_test with invalid patch"""
        executor = PatchExecutor(repo_root=str(tmp_path))
        
        # Create a plan item with invalid patch
        plan_item = PlanItem(
            id="test-3",
            title="Test invalid patch",
            action="edit_file",
            target="nonexistent.py",
            patch="invalid patch content"
        )
        
        result = executor.apply_patch_and_test(plan_item)
        
        assert isinstance(result, dict)
        assert result["ok"] is False
        assert "error" in result
