"""
Test suite for Learning Rollback Manager v2
"""

import json
import tempfile
from pathlib import Path

import pytest

pytest.skip("Module not available", allow_module_level=True)

from stillme_core.learning.rollback_manager import (
    LearningSnapshot,
    RollbackManager,
    RollbackReason,
    SandboxResult,
    SandboxStatus,
)


class TestRollbackManager:
    """Test cases for RollbackManager"""

    @pytest.fixture
    def temp_snapshots_dir(self):
        """Create temporary snapshots directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshots_dir = Path(temp_dir) / "snapshots"
            snapshots_dir.mkdir()
            yield snapshots_dir

    @pytest.fixture
    def temp_sandbox_dir(self):
        """Create temporary sandbox directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_dir = Path(temp_dir) / "sandbox"
            sandbox_dir.mkdir()
            yield sandbox_dir

    @pytest.fixture
    def rollback_manager(self, temp_snapshots_dir, temp_sandbox_dir):
        """Create RollbackManager instance for testing"""
        return RollbackManager(
            snapshots_dir=str(temp_snapshots_dir),
            sandbox_dir=str(temp_sandbox_dir)
        )

    @pytest.fixture
    def sample_model_state(self):
        """Sample model state for testing"""
        return {
            "weights": {"layer1": [0.1, 0.2, 0.3], "layer2": [0.4, 0.5, 0.6]},
            "parameters": {"learning_rate": 0.001, "batch_size": 32},
            "version": "1.0.0"
        }

    @pytest.fixture
    def sample_learning_data(self):
        """Sample learning data for testing"""
        return {
            "training_data": ["sample1", "sample2", "sample3"],
            "validation_data": ["val1", "val2"],
            "hyperparameters": {"epochs": 10, "optimizer": "adam"}
        }

    def test_initialization(self, rollback_manager):
        """Test RollbackManager initialization"""
        assert rollback_manager.snapshots_dir.exists()
        assert rollback_manager.sandbox_dir.exists()
        assert isinstance(rollback_manager.snapshots, dict)

    @pytest.mark.asyncio
    async def test_create_snapshot(self, rollback_manager, sample_model_state, sample_learning_data):
        """Test creating a learning snapshot"""
        performance_metrics = {"accuracy": 0.85, "f1_score": 0.82}
        ethics_scores = {"overall": 0.9, "bias_score": 0.88}
        safety_metrics = {"overall": 0.92, "safety_score": 0.91}

        version_id = await rollback_manager.create_snapshot(
            model_state=sample_model_state,
            learning_data=sample_learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            description="Test snapshot"
        )

        assert version_id is not None
        assert version_id in rollback_manager.snapshots

        snapshot = rollback_manager.snapshots[version_id]
        assert snapshot.model_state == sample_model_state
        assert snapshot.learning_data == sample_learning_data
        assert snapshot.performance_metrics == performance_metrics
        assert snapshot.ethics_scores == ethics_scores
        assert snapshot.safety_metrics == safety_metrics
        assert snapshot.description == "Test snapshot"

    @pytest.mark.asyncio
    async def test_create_multiple_snapshots(self, rollback_manager, sample_model_state, sample_learning_data):
        """Test creating multiple snapshots"""
        performance_metrics = {"accuracy": 0.85}
        ethics_scores = {"overall": 0.9}
        safety_metrics = {"overall": 0.92}

        # Create first snapshot
        version_id_1 = await rollback_manager.create_snapshot(
            model_state=sample_model_state,
            learning_data=sample_learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            description="First snapshot"
        )

        # Create second snapshot
        version_id_2 = await rollback_manager.create_snapshot(
            model_state=sample_model_state,
            learning_data=sample_learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            description="Second snapshot"
        )

        assert version_id_1 != version_id_2
        assert len(rollback_manager.snapshots) == 2
        assert version_id_1 in rollback_manager.snapshots
        assert version_id_2 in rollback_manager.snapshots

    @pytest.mark.asyncio
    async def test_execute_in_sandbox(self, rollback_manager, sample_model_state, sample_learning_data):
        """Test sandbox execution"""
        # Create baseline snapshot
        performance_metrics = {"accuracy": 0.85}
        ethics_scores = {"overall": 0.9}
        safety_metrics = {"overall": 0.92}

        baseline_version = await rollback_manager.create_snapshot(
            model_state=sample_model_state,
            learning_data=sample_learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            description="Baseline snapshot"
        )

        # Execute in sandbox
        learning_update = {
            "new_weights": [0.1, 0.2, 0.3],
            "new_parameters": {"learning_rate": 0.002}
        }

        result = await rollback_manager.execute_in_sandbox(
            learning_update=learning_update,
            baseline_snapshot=baseline_version,
            timeout=60
        )

        assert isinstance(result, SandboxResult)
        assert result.sandbox_id is not None
        assert result.status in [SandboxStatus.COMPLETED, SandboxStatus.ROLLED_BACK, SandboxStatus.FAILED]
        assert result.execution_time > 0
        assert isinstance(result.rollback_required, bool)

    @pytest.mark.asyncio
    async def test_execute_in_sandbox_with_nonexistent_baseline(self, rollback_manager):
        """Test sandbox execution with non-existent baseline"""
        learning_update = {"test": "data"}

        with pytest.raises(ValueError, match="Baseline snapshot nonexistent not found"):
            await rollback_manager.execute_in_sandbox(
                learning_update=learning_update,
                baseline_snapshot="nonexistent",
                timeout=60
            )

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, rollback_manager, sample_model_state, sample_learning_data):
        """Test rollback to specific version"""
        # Create snapshot
        performance_metrics = {"accuracy": 0.85}
        ethics_scores = {"overall": 0.9}
        safety_metrics = {"overall": 0.92}

        version_id = await rollback_manager.create_snapshot(
            model_state=sample_model_state,
            learning_data=sample_learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            description="Test snapshot"
        )

        # Rollback to version
        success = await rollback_manager.rollback_to_version(
            version_id=version_id,
            reason=RollbackReason.USER_REQUEST
        )

        assert success

        # Check that a new rollback snapshot was created
        assert len(rollback_manager.snapshots) == 2
        rollback_snapshots = [s for s in rollback_manager.snapshots.values()
                             if "rollback" in s.description.lower()]
        assert len(rollback_snapshots) == 1
        assert rollback_snapshots[0].description.endswith("user_request")

    @pytest.mark.asyncio
    async def test_rollback_to_nonexistent_version(self, rollback_manager):
        """Test rollback to non-existent version"""
        success = await rollback_manager.rollback_to_version(
            version_id="nonexistent",
            reason=RollbackReason.USER_REQUEST
        )

        assert not success

    def test_get_snapshot_history(self, rollback_manager):
        """Test getting snapshot history"""
        # Initially empty
        history = rollback_manager.get_snapshot_history()
        assert len(history) == 0

        # Add some snapshots (simulate)
        snapshot1 = LearningSnapshot(
            version_id="v1",
            timestamp="2025-09-26T10:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={"accuracy": 0.8},
            ethics_scores={"overall": 0.9},
            safety_metrics={"overall": 0.9},
            checksum="abc123",
            description="Snapshot 1"
        )

        snapshot2 = LearningSnapshot(
            version_id="v2",
            timestamp="2025-09-26T11:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={"accuracy": 0.85},
            ethics_scores={"overall": 0.92},
            safety_metrics={"overall": 0.91},
            checksum="def456",
            description="Snapshot 2"
        )

        rollback_manager.snapshots["v1"] = snapshot1
        rollback_manager.snapshots["v2"] = snapshot2

        history = rollback_manager.get_snapshot_history()
        assert len(history) == 2
        assert history[0]["version_id"] == "v1"  # Should be sorted by timestamp
        assert history[1]["version_id"] == "v2"

    def test_get_latest_snapshot(self, rollback_manager):
        """Test getting latest snapshot"""
        # Initially None
        latest = rollback_manager.get_latest_snapshot()
        assert latest is None

        # Add snapshots
        snapshot1 = LearningSnapshot(
            version_id="v1",
            timestamp="2025-09-26T10:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={},
            ethics_scores={},
            safety_metrics={},
            checksum="abc123",
            description="Snapshot 1"
        )

        snapshot2 = LearningSnapshot(
            version_id="v2",
            timestamp="2025-09-26T11:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={},
            ethics_scores={},
            safety_metrics={},
            checksum="def456",
            description="Snapshot 2"
        )

        rollback_manager.snapshots["v1"] = snapshot1
        rollback_manager.snapshots["v2"] = snapshot2

        latest = rollback_manager.get_latest_snapshot()
        assert latest is not None
        assert latest.version_id == "v2"  # Should be the latest by timestamp

    def test_get_snapshot_by_id(self, rollback_manager):
        """Test getting snapshot by ID"""
        # Non-existent ID
        snapshot = rollback_manager.get_snapshot_by_id("nonexistent")
        assert snapshot is None

        # Add snapshot
        test_snapshot = LearningSnapshot(
            version_id="test_v1",
            timestamp="2025-09-26T10:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={},
            ethics_scores={},
            safety_metrics={},
            checksum="test123",
            description="Test snapshot"
        )

        rollback_manager.snapshots["test_v1"] = test_snapshot

        # Get by ID
        snapshot = rollback_manager.get_snapshot_by_id("test_v1")
        assert snapshot is not None
        assert snapshot.version_id == "test_v1"

    @pytest.mark.asyncio
    async def test_export_snapshot_data(self, rollback_manager, temp_snapshots_dir):
        """Test exporting snapshot data"""
        # Create snapshot
        test_snapshot = LearningSnapshot(
            version_id="export_test",
            timestamp="2025-09-26T10:00:00Z",
            model_state={"test": "data"},
            learning_data={"learning": "data"},
            performance_metrics={"accuracy": 0.9},
            ethics_scores={"overall": 0.95},
            safety_metrics={"overall": 0.93},
            checksum="export123",
            description="Export test snapshot"
        )

        rollback_manager.snapshots["export_test"] = test_snapshot

        # Export to file
        output_path = temp_snapshots_dir / "exported_snapshot.json"
        success = await rollback_manager.export_snapshot_data("export_test", str(output_path))

        assert success
        assert output_path.exists()

        # Verify exported data
        with open(output_path) as f:
            exported_data = json.load(f)

        assert exported_data["version_id"] == "export_test"
        assert exported_data["model_state"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_export_nonexistent_snapshot(self, rollback_manager):
        """Test exporting non-existent snapshot"""
        success = await rollback_manager.export_snapshot_data("nonexistent", "output.json")
        assert not success

    def test_get_rollback_statistics(self, rollback_manager):
        """Test getting rollback statistics"""
        # Initially empty
        stats = rollback_manager.get_rollback_statistics()
        assert stats["total_snapshots"] == 0
        assert stats["rollback_count"] == 0
        assert stats["latest_version"] is None
        assert stats["snapshot_health"] == "unknown"

        # Add snapshots with rollbacks
        snapshot1 = LearningSnapshot(
            version_id="v1",
            timestamp="2025-09-26T10:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={},
            ethics_scores={"overall": 0.9},
            safety_metrics={"overall": 0.9},
            checksum="abc123",
            description="Normal snapshot"
        )

        snapshot2 = LearningSnapshot(
            version_id="v2",
            timestamp="2025-09-26T11:00:00Z",
            model_state={},
            learning_data={},
            performance_metrics={},
            ethics_scores={"overall": 0.95},
            safety_metrics={"overall": 0.95},
            checksum="def456",
            description="Rollback to v1 - user_request"
        )

        rollback_manager.snapshots["v1"] = snapshot1
        rollback_manager.snapshots["v2"] = snapshot2

        stats = rollback_manager.get_rollback_statistics()
        assert stats["total_snapshots"] == 2
        assert stats["rollback_count"] == 1
        assert stats["latest_version"] == "v2"
        assert stats["snapshot_health"] == "good"  # Less than 30% rollbacks
        assert stats["average_ethics_score"] == 0.925  # (0.9 + 0.95) / 2
        assert stats["average_safety_score"] == 0.925  # (0.9 + 0.95) / 2

class TestLearningSnapshot:
    """Test cases for LearningSnapshot dataclass"""

    def test_learning_snapshot_creation(self):
        """Test LearningSnapshot creation"""
        snapshot = LearningSnapshot(
            version_id="test_v1",
            timestamp="2025-09-26T10:00:00Z",
            model_state={"weights": [0.1, 0.2]},
            learning_data={"epochs": 10},
            performance_metrics={"accuracy": 0.85},
            ethics_scores={"overall": 0.9},
            safety_metrics={"overall": 0.92},
            checksum="abc123",
            description="Test snapshot"
        )

        assert snapshot.version_id == "test_v1"
        assert snapshot.timestamp == "2025-09-26T10:00:00Z"
        assert snapshot.model_state["weights"] == [0.1, 0.2]
        assert snapshot.performance_metrics["accuracy"] == 0.85
        assert snapshot.checksum == "abc123"
        assert snapshot.description == "Test snapshot"

class TestSandboxResult:
    """Test cases for SandboxResult dataclass"""

    def test_sandbox_result_creation(self):
        """Test SandboxResult creation"""
        result = SandboxResult(
            sandbox_id="test_sandbox",
            status=SandboxStatus.COMPLETED,
            execution_time=1.5,
            performance_delta=0.1,
            ethics_score=0.9,
            safety_score=0.95,
            errors=[],
            warnings=["Minor warning"],
            rollback_required=False,
            rollback_reason=None
        )

        assert result.sandbox_id == "test_sandbox"
        assert result.status == SandboxStatus.COMPLETED
        assert result.execution_time == 1.5
        assert result.performance_delta == 0.1
        assert result.ethics_score == 0.9
        assert result.safety_score == 0.95
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert not result.rollback_required
        assert result.rollback_reason is None

@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete rollback workflow"""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshots_dir = Path(temp_dir) / "snapshots"
        sandbox_dir = Path(temp_dir) / "sandbox"
        snapshots_dir.mkdir()
        sandbox_dir.mkdir()

        # Create manager
        manager = RollbackManager(
            snapshots_dir=str(snapshots_dir),
            sandbox_dir=str(sandbox_dir)
        )

        # Create initial snapshot
        model_state = {"weights": [0.1, 0.2, 0.3]}
        learning_data = {"epochs": 10}
        performance_metrics = {"accuracy": 0.8}
        ethics_scores = {"overall": 0.9}
        safety_metrics = {"overall": 0.9}

        version_id = await manager.create_snapshot(
            model_state=model_state,
            learning_data=learning_data,
            performance_metrics=performance_metrics,
            ethics_scores=ethics_scores,
            safety_metrics=safety_metrics,
            description="Initial snapshot"
        )

        # Execute sandbox test
        learning_update = {"new_weights": [0.2, 0.3, 0.4]}
        result = await manager.execute_in_sandbox(
            learning_update=learning_update,
            baseline_snapshot=version_id,
            timeout=60
        )

        # Verify sandbox result
        assert result.sandbox_id is not None
        assert result.status in [SandboxStatus.COMPLETED, SandboxStatus.ROLLED_BACK, SandboxStatus.FAILED]

        # Test rollback if needed
        if result.rollback_required:
            rollback_success = await manager.rollback_to_version(
                version_id=version_id,
                reason=result.rollback_reason or RollbackReason.AUTOMATIC_SAFETY
            )
            assert rollback_success

        # Verify statistics
        stats = manager.get_rollback_statistics()
        assert stats["total_snapshots"] >= 1
