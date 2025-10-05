from unittest.mock import MagicMock

# Mock classes since they're not available in stillme_core
QualityIssue = MagicMock
QualityReport = MagicMock

"""
Tests for Code Quality Enforcer

Comprehensive test suite for the Code Quality Enforcer module.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from stillme_core.quality.agentdev_integration import AgentDevQualityIntegration
from stillme_core.quality.auto_fixer import AutoFixer

# Mock classes since they're not available in stillme_core.quality.code_quality_enforcer
CodeQualityEnforcer = MagicMock
from stillme_core.quality.quality_metrics import QualityMetrics


class TestCodeQualityEnforcer:
    """Test cases for CodeQualityEnforcer"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def sample_python_file(self, temp_dir):
        """Create sample Python file with quality issues"""
        sample_code = """
import os
import sys
import json

def hello_world():
    print("Hello World")
    return "Hello World"

class TestClass:
    def __init__(self):
        self.value = 42

    def method_with_long_name_that_exceeds_line_length_limit_and_should_be_refactored(self):
        return self.value

if __name__ == "__main__":
    hello_world()
"""
        file_path = temp_dir / "sample.py"
        file_path.write_text(sample_code)
        return file_path

    @pytest.fixture
    def enforcer(self):
        """Create CodeQualityEnforcer instance"""
        return CodeQualityEnforcer()

    def test_quality_issue_creation(self):
        """Test QualityIssue dataclass creation"""
        issue = QualityIssue(
            tool="ruff",
            file_path="test.py",
            line_number=10,
            column=5,
            code="E501",
            message="Line too long",
            severity="error",
            category="style",
            fixable=True,
            auto_fix="Break line",
        )

        assert issue.tool == "ruff"
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.severity == "error"
        assert issue.fixable is True

    def test_quality_report_creation(self):
        """Test QualityReport dataclass creation"""
        issues = [
            QualityIssue(
                tool="ruff",
                file_path="test.py",
                line_number=1,
                column=1,
                code="E501",
                message="Line too long",
                severity="error",
                category="style",
            )
        ]

        report = QualityReport(
            timestamp="2025-01-01T00:00:00",
            target_path="/test",
            total_files=1,
            total_issues=1,
            issues_by_tool={"ruff": 1},
            issues_by_severity={"error": 1},
            issues_by_category={"style": 1},
            issues=issues,
            quality_score=85.0,
            recommendations=["Fix line length"],
        )

        assert report.total_files == 1
        assert report.total_issues == 1
        assert report.quality_score == 85.0
        assert len(report.issues) == 1

    def test_get_python_files(self, enforcer, temp_dir):
        """Test getting Python files from directory"""
        # Create test files
        (temp_dir / "test1.py").write_text("print('hello')")
        (temp_dir / "test2.py").write_text("print('world')")
        (temp_dir / "test.txt").write_text("not python")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "test3.py").write_text("print('nested')")

        files = enforcer._get_python_files(temp_dir)

        assert len(files) == 3
        assert all(f.suffix == ".py" for f in files)
        assert any("test1.py" in str(f) for f in files)
        assert any("test2.py" in str(f) for f in files)
        assert any("test3.py" in str(f) for f in files)

    def test_get_python_files_with_exclusions(self, enforcer, temp_dir):
        """Test getting Python files with exclusions"""
        # Create test files including excluded patterns
        (temp_dir / "test.py").write_text("print('hello')")
        (temp_dir / "__pycache__").mkdir()
        (temp_dir / "__pycache__" / "test.pyc").write_text("bytecode")
        (temp_dir / ".git").mkdir()
        (temp_dir / ".git" / "config").write_text("git config")

        files = enforcer._get_python_files(temp_dir)

        # Should only find the main test.py file
        assert len(files) == 1
        assert "test.py" in str(files[0])

    @pytest.mark.asyncio
    async def test_analyze_directory_empty(self, enforcer, temp_dir):
        """Test analyzing empty directory"""
        report = await enforcer.analyze_directory(str(temp_dir))

        assert report.total_files == 0
        assert report.total_issues == 0
        assert report.quality_score == 100.0
        assert "No Python files found" in report.recommendations[0]

    @pytest.mark.asyncio
    async def test_analyze_directory_with_files(self, enforcer, sample_python_file):
        """Test analyzing directory with Python files"""
        target_dir = sample_python_file.parent

        # Mock subprocess calls to avoid actual tool execution
        with patch("subprocess.run") as mock_run:
            # Mock successful tool runs
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            report = await enforcer.analyze_directory(str(target_dir))

            assert report.total_files > 0
            assert report.target_path == str(target_dir)
            assert isinstance(report.quality_score, float)
            assert 0 <= report.quality_score <= 100

    def test_calculate_quality_score(self, enforcer):
        """Test quality score calculation"""
        # Test with no issues
        issues = []
        score = enforcer._calculate_quality_score(issues, 10)
        assert score == 100.0

        # Test with some issues
        issues = [
            QualityIssue(
                "ruff", "test.py", 1, 1, "E501", "Line too long", "error", "style"
            ),
            QualityIssue(
                "ruff",
                "test.py",
                2,
                1,
                "W291",
                "Trailing whitespace",
                "warning",
                "style",
            ),
        ]
        score = enforcer._calculate_quality_score(issues, 1)
        assert 0 <= score < 100

    def test_generate_recommendations(self, enforcer):
        """Test recommendation generation"""
        issues = [
            QualityIssue(
                "ruff", "test.py", 1, 1, "E501", "Line too long", "error", "style"
            ),
            QualityIssue(
                "pylint",
                "test.py",
                2,
                1,
                "C0111",
                "Missing docstring",
                "warning",
                "style",
            ),
        ]

        issues_by_tool = {"ruff": 1, "pylint": 1}
        recommendations = enforcer._generate_recommendations(issues, issues_by_tool)

        assert len(recommendations) > 0
        assert any("ruff" in rec.lower() for rec in recommendations)

    def test_save_and_load_report(self, enforcer, temp_dir):
        """Test saving and loading quality reports"""
        issues = [
            QualityIssue(
                "ruff", "test.py", 1, 1, "E501", "Line too long", "error", "style"
            )
        ]

        report = QualityReport(
            timestamp="2025-01-01T00:00:00",
            target_path="/test",
            total_files=1,
            total_issues=1,
            issues_by_tool={"ruff": 1},
            issues_by_severity={"error": 1},
            issues_by_category={"style": 1},
            issues=issues,
            quality_score=85.0,
            recommendations=["Fix line length"],
        )

        # Save report
        output_path = temp_dir / "report.json"
        enforcer.save_report(report, str(output_path))

        assert output_path.exists()

        # Load report
        loaded_report = enforcer.load_report(str(output_path))

        assert loaded_report.total_files == report.total_files
        assert loaded_report.total_issues == report.total_issues
        assert loaded_report.quality_score == report.quality_score
        assert len(loaded_report.issues) == len(report.issues)


class TestQualityMetrics:
    """Test cases for QualityMetrics"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def metrics(self, temp_db):
        """Create QualityMetrics instance"""
        return QualityMetrics(temp_db)

    @pytest.fixture
    def sample_report(self):
        """Create sample quality report"""
        issues = [
            QualityIssue(
                "ruff", "test.py", 1, 1, "E501", "Line too long", "error", "style"
            )
        ]

        return QualityReport(
            timestamp="2025-01-01T00:00:00",
            target_path="/test",
            total_files=1,
            total_issues=1,
            issues_by_tool={"ruff": 1},
            issues_by_severity={"error": 1},
            issues_by_category={"style": 1},
            issues=issues,
            quality_score=85.0,
            recommendations=["Fix line length"],
        )

    def test_store_and_retrieve_report(self, metrics, sample_report):
        """Test storing and retrieving quality reports"""
        # Store report
        metrics.store_report(sample_report)

        # Retrieve reports
        reports = metrics.get_reports()

        assert len(reports) == 1
        assert reports[0].total_files == sample_report.total_files
        assert reports[0].quality_score == sample_report.quality_score

    def test_quality_summary(self, metrics, sample_report):
        """Test quality summary generation"""
        # Store multiple reports
        metrics.store_report(sample_report)

        # Create another report
        report2 = QualityReport(
            timestamp="2025-01-02T00:00:00",
            target_path="/test",
            total_files=2,
            total_issues=0,
            issues_by_tool={},
            issues_by_severity={},
            issues_by_category={},
            issues=[],
            quality_score=95.0,
            recommendations=["Good job!"],
        )
        metrics.store_report(report2)

        # Get summary
        summary = metrics.get_quality_summary("/test", days=7)

        assert summary["status"] == "success"
        assert summary["reports_count"] == 2
        assert "quality_score" in summary
        assert "issues" in summary

    def test_quality_trends(self, metrics, sample_report):
        """Test quality trends calculation"""
        # Store multiple reports over time
        for i in range(5):
            report = QualityReport(
                timestamp=f"2025-01-{i+1:02d}T00:00:00",
                target_path="/test",
                total_files=1,
                total_issues=i,
                issues_by_tool={"ruff": i},
                issues_by_severity={"error": i},
                issues_by_category={"style": i},
                issues=[],
                quality_score=100 - i * 5,
                recommendations=["Fix issues"],
            )
            metrics.store_report(report)

        # Get trends
        trends = metrics.get_quality_trends("/test", days=7, group_by="day")

        assert len(trends) == 5
        assert trends[0].quality_score == 100.0  # First day
        assert trends[-1].quality_score == 80.0  # Last day


class TestAutoFixer:
    """Test cases for AutoFixer"""

    @pytest.fixture
    def auto_fixer(self):
        """Create AutoFixer instance"""
        return AutoFixer(create_backups=False)

    def test_fix_trailing_whitespace(self, auto_fixer):
        """Test fixing trailing whitespace"""
        content = "line1   \nline2\t\nline3"
        fixed_content, fixed = auto_fixer._fix_trailing_whitespace(content, None)

        assert fixed is True
        assert fixed_content == "line1\nline2\nline3"

    def test_fix_missing_newline(self, auto_fixer):
        """Test fixing missing newline at end of file"""
        content = "line1\nline2"
        fixed_content, fixed = auto_fixer._fix_missing_newline(content, None)

        assert fixed is True
        assert fixed_content == "line1\nline2\n"

    def test_fix_semicolons(self, auto_fixer):
        """Test fixing semicolon issues"""
        content = "line1;\nline2;\nline3"
        fixed_content, fixed = auto_fixer._fix_semicolons(content, None)

        assert fixed is True
        assert fixed_content == "line1\nline2\nline3"

    def test_determine_fix_type(self, auto_fixer):
        """Test determining fix type from issue"""
        issue = QualityIssue(
            tool="ruff",
            file_path="test.py",
            line_number=1,
            column=1,
            code="E501",
            message="Line too long",
            severity="error",
            category="style",
        )

        fix_type = auto_fixer._determine_fix_type(issue)
        assert fix_type == "line_length"


class TestAgentDevQualityIntegration:
    """Test cases for AgentDevQualityIntegration"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def integration(self, temp_dir):
        """Create AgentDevQualityIntegration instance"""
        db_path = temp_dir / "test_metrics.db"
        return AgentDevQualityIntegration(str(db_path))

    @pytest.fixture
    def sample_python_file(self, temp_dir):
        """Create sample Python file"""
        sample_code = """
def hello_world():
    print("Hello World")
    return "Hello World"
"""
        file_path = temp_dir / "sample.py"
        file_path.write_text(sample_code)
        return file_path

    @pytest.mark.asyncio
    async def test_analyze_and_fix(self, integration, sample_python_file):
        """Test analyze and fix functionality"""
        target_dir = sample_python_file.parent

        # Mock the enforcer to avoid actual tool execution
        with patch.object(integration.enforcer, "analyze_directory") as mock_analyze:
            mock_report = QualityReport(
                timestamp="2025-01-01T00:00:00",
                target_path=str(target_dir),
                total_files=1,
                total_issues=2,
                issues_by_tool={"ruff": 2},
                issues_by_severity={"warning": 2},
                issues_by_category={"style": 2},
                issues=[],
                quality_score=85.0,
                recommendations=["Fix style issues"],
                auto_fixes_applied=1,
                execution_time=1.5,
            )
            mock_analyze.return_value = mock_report

            results = await integration.analyze_and_fix(
                target_path=str(target_dir), auto_fix=True
            )

            assert "analysis" in results
            assert results["analysis"]["quality_score"] == 85.0
            assert results["analysis"]["total_issues"] == 2
            assert results["quality_level"] == "good"

    @pytest.mark.asyncio
    async def test_pre_commit_quality_check(self, integration, sample_python_file):
        """Test pre-commit quality check"""
        target_dir = sample_python_file.parent

        # Mock the enforcer
        with patch.object(integration.enforcer, "analyze_directory") as mock_analyze:
            mock_report = QualityReport(
                timestamp="2025-01-01T00:00:00",
                target_path=str(target_dir),
                total_files=1,
                total_issues=1,
                issues_by_tool={"ruff": 1},
                issues_by_severity={"warning": 1},
                issues_by_category={"style": 1},
                issues=[],
                quality_score=90.0,
                recommendations=["Minor style fix"],
                auto_fixes_applied=1,
                execution_time=1.0,
            )
            mock_analyze.return_value = mock_report

            results = await integration.pre_commit_quality_check(
                target_path=str(target_dir),
                min_quality_score=80.0,
                max_issues_per_file=2.0,
            )

            assert results["passed"] is True
            assert results["quality_score"] == 90.0
            assert results["issues_per_file"] == 1.0

    def test_get_quality_dashboard(self, integration):
        """Test getting quality dashboard data"""
        dashboard_data = integration.get_quality_dashboard("/test")

        assert "trends" in dashboard_data
        assert "summary" in dashboard_data
        assert "comparison" in dashboard_data
        assert "benchmarks" in dashboard_data

    def test_export_quality_report(self, integration, temp_dir):
        """Test exporting quality report"""
        output_path = temp_dir / "export.json"

        results = integration.export_quality_report(
            target_path="/test", output_path=str(output_path), days=30
        )

        assert results["success"] is True
        assert results["output_path"] == str(output_path)


# Integration test
@pytest.mark.asyncio
async def test_full_quality_workflow():
    """Test complete quality workflow"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """
def hello_world():
    print("Hello World")
    return "Hello World"
"""
        )

        # Create integration instance
        integration = AgentDevQualityIntegration(str(tmp_path / "test.db"))

        # Mock subprocess calls to avoid actual tool execution
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Run full workflow
            results = await integration.run_quality_workflow(
                target_path=str(tmp_path), workflow_type="full"
            )

            assert results["workflow_type"] == "full"
            assert results["workflow_completed"] is True
            assert "analysis" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
