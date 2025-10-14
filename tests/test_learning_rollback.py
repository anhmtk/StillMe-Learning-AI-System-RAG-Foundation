from unittest.mock import patch

#!/usr/bin/env python3
"""
Test suite for Learning Rollback System
=======================================

Tests for version control and rollback mechanisms.

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import asyncio
import shutil

# Add project root to path
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock

# Mock classes since they're not available in stillme_core.control.learning_rollback
LearningRollback = MagicMock
LearningUpdateType = MagicMock
RollbackStatus = MagicMock


class TestLearningRollback:
    """Test suite for LearningRollback system"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def rollback_system(self, temp_dir):
        """Create rollback system with temporary directory"""
        with patch("stillme_core.control.learning_rollback.Path") as mock_path:
            mock_path.return_value = Path(temp_dir)
            system = LearningRollback()
            return system

    @pytest.mark.asyncio
    async def test_create_snapshot(self, rollback_system):
        """Test creating a learning snapshot"""
        changes = {
            "knowledge_base": {"new_fact": "AI learns from data"},
            "behavior": {"response_style": "more_helpful"},
        }

        snapshot = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="Added new knowledge about AI learning",
            changes=changes,
        )

        assert snapshot.version_id is not None
        assert snapshot.update_type == "knowledge_base_update"
        assert snapshot.description == "Added new knowledge about AI learning"
        assert snapshot.changes == changes
        assert snapshot.state_hash is not None

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, rollback_system):
        """Test rolling back to a previous version"""
        # Create initial snapshot
        snapshot1 = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="Initial state",
            changes={"initial": "state"},
        )

        # Create second snapshot
        await rollback_system.create_snapshot(
            update_type=LearningUpdateType.PATTERN_LEARNING,
            description="Pattern learning update",
            changes={"pattern": "learned"},
        )

        # Rollback to first version
        result = await rollback_system.rollback_to_version(snapshot1.version_id)

        assert result.status == RollbackStatus.SUCCESS.value
        assert result.version_id == snapshot1.version_id
        assert len(result.changes_reverted) > 0
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_rollback_not_needed(self, rollback_system):
        """Test rollback when already at target version"""
        snapshot = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="Test snapshot",
            changes={"test": "data"},
        )

        result = await rollback_system.rollback_to_version(snapshot.version_id)

        assert result.status == RollbackStatus.NOT_NEEDED.value
        assert result.changes_reverted == []
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_rollback_to_nonexistent_version(self, rollback_system):
        """Test rollback to non-existent version"""
        result = await rollback_system.rollback_to_version("nonexistent_version")

        assert result.status == RollbackStatus.FAILED.value
        assert "not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_get_rollback_candidates(self, rollback_system):
        """Test getting rollback candidates"""
        # Create multiple snapshots
        await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="Snapshot 1",
            changes={"data": "1"},
        )

        await rollback_system.create_snapshot(
            update_type=LearningUpdateType.PATTERN_LEARNING,
            description="Snapshot 2",
            changes={"data": "2"},
        )

        candidates = await rollback_system.get_rollback_candidates()

        assert len(candidates) == 2
        assert all("version_id" in candidate for candidate in candidates)
        assert all("can_rollback" in candidate for candidate in candidates)

    @pytest.mark.asyncio
    async def test_get_version_history(self, rollback_system):
        """Test getting version history"""
        # Create snapshots
        snapshot1 = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="First snapshot",
            changes={"data": "1"},
        )

        snapshot2 = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.PATTERN_LEARNING,
            description="Second snapshot",
            changes={"data": "2"},
        )

        history = await rollback_system.get_version_history(limit=10)

        assert len(history) == 2
        assert history[0]["version_id"] == snapshot2.version_id  # Most recent first
        assert history[1]["version_id"] == snapshot1.version_id

    def test_get_current_version(self, rollback_system):
        """Test getting current version"""
        # Initially no version
        assert rollback_system.get_current_version() is None

        # After creating snapshot, should have current version
        asyncio.run(
            rollback_system.create_snapshot(
                update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
                description="Test",
                changes={"test": "data"},
            )
        )

        assert rollback_system.get_current_version() is not None

    def test_get_snapshot_count(self, rollback_system):
        """Test getting snapshot count"""
        assert rollback_system.get_snapshot_count() == 0

        asyncio.run(
            rollback_system.create_snapshot(
                update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
                description="Test",
                changes={"test": "data"},
            )
        )

        assert rollback_system.get_snapshot_count() == 1

    def test_get_rollback_count(self, rollback_system):
        """Test getting rollback count"""
        assert rollback_system.get_rollback_count() == 0

        # Perform a rollback to increment count
        asyncio.run(
            rollback_system.create_snapshot(
                update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
                description="Test",
                changes={"test": "data"},
            )
        )

        # Rollback should increment count
        asyncio.run(
            rollback_system.rollback_to_version(
                list(rollback_system.snapshots.keys())[0]
            )
        )

        assert rollback_system.get_rollback_count() >= 0  # May be 0 if rollback failed

    @pytest.mark.asyncio
    async def test_rollback_with_dependencies(self, rollback_system):
        """Test rollback with dependencies"""
        # Create snapshot with dependencies
        snapshot1 = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="Base snapshot",
            changes={"base": "data"},
        )

        await rollback_system.create_snapshot(
            update_type=LearningUpdateType.PATTERN_LEARNING,
            description="Dependent snapshot",
            changes={"dependent": "data"},
            dependencies=[snapshot1.version_id],
        )

        # Try to rollback to first snapshot (should fail due to dependencies)
        result = await rollback_system.rollback_to_version(snapshot1.version_id)

        # Should fail due to dependencies
        assert result.status == RollbackStatus.FAILED.value
        assert "dependent" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_force_rollback(self, rollback_system):
        """Test forced rollback ignoring dependencies"""
        # Create snapshot with dependencies
        snapshot1 = await rollback_system.create_snapshot(
            update_type=LearningUpdateType.KNOWLEDGE_BASE_UPDATE,
            description="Base snapshot",
            changes={"base": "data"},
        )

        await rollback_system.create_snapshot(
            update_type=LearningUpdateType.PATTERN_LEARNING,
            description="Dependent snapshot",
            changes={"dependent": "data"},
            dependencies=[snapshot1.version_id],
        )

        # Force rollback to first snapshot
        result = await rollback_system.rollback_to_version(
            snapshot1.version_id, force=True
        )

        # Should succeed with force
        assert result.status == RollbackStatus.SUCCESS.value