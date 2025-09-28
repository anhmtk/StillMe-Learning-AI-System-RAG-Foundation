"""
Test Unified Learning System
============================

Tests for the unified learning manager that resolves conflicts between
old and new learning systems.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from stillme_core.learning.unified_learning_manager import (
    UnifiedLearningManager, 
    LearningSystemMode, 
    LearningConfig
)
from stillme_core.learning.interface import (
    OldLearningAdapter, 
    NewLearningAdapter
)


class TestUnifiedLearningManager:
    """Test unified learning manager"""
    
    def test_init_with_config_file(self):
        """Test initialization with config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            config_content = """
            system = "new"
            [migration]
            auto_migrate = true
            backup_before_migrate = true
            [compatibility]
            conflict_resolution = "new_wins"
            """
            f.write(config_content)
            f.flush()
            
            manager = UnifiedLearningManager(f.name)
            assert manager.config.mode == LearningSystemMode.NEW_ONLY
            assert manager.config.auto_migrate is True
            assert manager.config.conflict_resolution == "new_wins"
    
    def test_init_without_config_file(self):
        """Test initialization without config file"""
        with patch('pathlib.Path.exists', return_value=False):
            manager = UnifiedLearningManager("nonexistent.toml")
            assert manager.config.mode == LearningSystemMode.NEW_ONLY
    
    @patch('stillme_core.learning.unified_learning_manager.OldLearningAdapter')
    @patch('stillme_core.learning.unified_learning_manager.NewLearningAdapter')
    def test_initialize_adapters_old_only(self, mock_new_adapter, mock_old_adapter):
        """Test adapter initialization in old-only mode"""
        # Create manager without initializing adapters
        manager = UnifiedLearningManager.__new__(UnifiedLearningManager)
        manager.config = LearningConfig(mode=LearningSystemMode.OLD_ONLY)
        manager.old_adapter = None
        manager.new_adapter = None

        manager._initialize_adapters()

        mock_old_adapter.assert_called_once()
        mock_new_adapter.assert_not_called()
    
    @patch('stillme_core.learning.unified_learning_manager.OldLearningAdapter')
    @patch('stillme_core.learning.unified_learning_manager.NewLearningAdapter')
    def test_initialize_adapters_new_only(self, mock_new_adapter, mock_old_adapter):
        """Test adapter initialization in new-only mode"""
        # Create manager without initializing adapters
        manager = UnifiedLearningManager.__new__(UnifiedLearningManager)
        manager.config = LearningConfig(mode=LearningSystemMode.NEW_ONLY)
        manager.old_adapter = None
        manager.new_adapter = None

        manager._initialize_adapters()

        mock_new_adapter.assert_called_once()
        mock_old_adapter.assert_not_called()
    
    @patch('stillme_core.learning.unified_learning_manager.OldLearningAdapter')
    @patch('stillme_core.learning.unified_learning_manager.NewLearningAdapter')
    def test_initialize_adapters_both_parallel(self, mock_new_adapter, mock_old_adapter):
        """Test adapter initialization in both-parallel mode"""
        # Create manager without initializing adapters
        manager = UnifiedLearningManager.__new__(UnifiedLearningManager)
        manager.config = LearningConfig(mode=LearningSystemMode.BOTH_PARALLEL)
        manager.old_adapter = None
        manager.new_adapter = None

        manager._initialize_adapters()

        mock_old_adapter.assert_called_once()
        mock_new_adapter.assert_called_once()
    
    def test_store_experience_old_only(self):
        """Test storing experience in old-only mode"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.OLD_ONLY
        
        # Mock old adapter
        mock_old_adapter = Mock()
        mock_old_adapter.store_experience.return_value = "old_exp_123"
        manager.old_adapter = mock_old_adapter
        
        experience_data = {
            "type": "learning",
            "context": {"test": "data"},
            "action": "test_action",
            "outcome": {"success": True}
        }
        
        results = manager.store_experience(experience_data)
        
        assert "old_system" in results
        assert results["old_system"] == "old_exp_123"
        mock_old_adapter.store_experience.assert_called_once_with(experience_data)
    
    def test_store_experience_new_only(self):
        """Test storing experience in new-only mode"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.NEW_ONLY
        
        # Mock new adapter
        mock_new_adapter = Mock()
        mock_new_adapter.store_experience.return_value = "new_exp_123"
        manager.new_adapter = mock_new_adapter
        
        experience_data = {
            "type": "learning",
            "context": {"test": "data"},
            "action": "test_action",
            "outcome": {"success": True}
        }
        
        results = manager.store_experience(experience_data)
        
        assert "new_system" in results
        assert results["new_system"] == "new_exp_123"
        mock_new_adapter.store_experience.assert_called_once_with(experience_data)
    
    def test_store_experience_both_parallel(self):
        """Test storing experience in both-parallel mode"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.BOTH_PARALLEL
        
        # Mock both adapters
        mock_old_adapter = Mock()
        mock_old_adapter.store_experience.return_value = "old_exp_123"
        manager.old_adapter = mock_old_adapter
        
        mock_new_adapter = Mock()
        mock_new_adapter.store_experience.return_value = "new_exp_123"
        manager.new_adapter = mock_new_adapter
        
        experience_data = {
            "type": "learning",
            "context": {"test": "data"},
            "action": "test_action",
            "outcome": {"success": True}
        }
        
        results = manager.store_experience(experience_data)
        
        assert "old_system" in results
        assert "new_system" in results
        assert results["old_system"] == "old_exp_123"
        assert results["new_system"] == "new_exp_123"
        
        mock_old_adapter.store_experience.assert_called_once_with(experience_data)
        mock_new_adapter.store_experience.assert_called_once_with(experience_data)
    
    def test_get_recommendations_old_only(self):
        """Test getting recommendations in old-only mode"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.OLD_ONLY
        
        # Mock old adapter
        mock_old_adapter = Mock()
        mock_old_adapter.get_recommendations.return_value = [
            {"id": "rec1", "confidence": 0.8},
            {"id": "rec2", "confidence": 0.6}
        ]
        manager.old_adapter = mock_old_adapter
        
        context = {"action": "test", "tags": ["test"]}
        recommendations = manager.get_recommendations(context)
        
        assert len(recommendations) == 2
        assert recommendations[0]["id"] == "rec1"
        mock_old_adapter.get_recommendations.assert_called_once_with(context)
    
    def test_get_recommendations_both_parallel(self):
        """Test getting recommendations in both-parallel mode"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.BOTH_PARALLEL
        
        # Mock both adapters
        mock_old_adapter = Mock()
        mock_old_adapter.get_recommendations.return_value = [
            {"id": "old_rec1", "confidence": 0.8}
        ]
        manager.old_adapter = mock_old_adapter
        
        mock_new_adapter = Mock()
        mock_new_adapter.get_recommendations.return_value = [
            {"id": "new_rec1", "confidence": 0.9}
        ]
        manager.new_adapter = mock_new_adapter
        
        context = {"action": "test", "tags": ["test"]}
        recommendations = manager.get_recommendations(context)
        
        assert len(recommendations) == 2
        assert any(rec["id"] == "old_rec1" and rec["source"] == "old_system" for rec in recommendations)
        assert any(rec["id"] == "new_rec1" and rec["source"] == "new_system" for rec in recommendations)
    
    def test_get_stats(self):
        """Test getting statistics from all systems"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.BOTH_PARALLEL
        
        # Mock both adapters
        mock_old_adapter = Mock()
        mock_old_adapter.get_stats.return_value = {"old_stats": "data"}
        manager.old_adapter = mock_old_adapter
        
        mock_new_adapter = Mock()
        mock_new_adapter.get_stats.return_value = {"new_stats": "data"}
        manager.new_adapter = mock_new_adapter
        
        stats = manager.get_stats()
        
        assert stats["mode"] == "both_parallel"
        assert "systems" in stats
        assert "old_system" in stats["systems"]
        assert "new_system" in stats["systems"]
        assert stats["systems"]["old_system"]["old_stats"] == "data"
        assert stats["systems"]["new_system"]["new_stats"] == "data"
    
    def test_cleanup(self):
        """Test cleanup of all systems"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.BOTH_PARALLEL
        
        # Mock both adapters
        mock_old_adapter = Mock()
        mock_old_adapter.cleanup.return_value = True
        manager.old_adapter = mock_old_adapter
        
        mock_new_adapter = Mock()
        mock_new_adapter.cleanup.return_value = True
        manager.new_adapter = mock_new_adapter
        
        result = manager.cleanup()
        
        assert result is True
        mock_old_adapter.cleanup.assert_called_once()
        mock_new_adapter.cleanup.assert_called_once()
    
    def test_switch_mode(self):
        """Test switching learning system mode"""
        manager = UnifiedLearningManager()
        manager.config.mode = LearningSystemMode.OLD_ONLY
        
        with patch.object(manager, '_initialize_adapters') as mock_init:
            result = manager.switch_mode(LearningSystemMode.NEW_ONLY)
            
            assert result is True
            assert manager.config.mode == LearningSystemMode.NEW_ONLY
            mock_init.assert_called_once()
    
    def test_migrate_data_placeholder(self):
        """Test data migration (placeholder implementation)"""
        manager = UnifiedLearningManager()
        manager.config.auto_migrate = True
        
        result = manager.migrate_data("old", "new")
        
        assert "status" in result
        assert result["from_system"] == "old"
        assert result["to_system"] == "new"
    
    def test_migrate_data_disabled(self):
        """Test data migration when disabled"""
        manager = UnifiedLearningManager()
        manager.config.auto_migrate = False
        
        result = manager.migrate_data("old", "new")
        
        assert "error" in result
        assert "disabled" in result["error"]


class TestLearningAdapters:
    """Test learning system adapters"""
    
    @patch('stillme_core.core.self_learning.experience_memory.ExperienceMemory')
    def test_old_learning_adapter_init(self, mock_experience_memory):
        """Test old learning adapter initialization"""
        adapter = OldLearningAdapter()
        
        mock_experience_memory.assert_called_once()
        assert adapter.experience_memory is not None
    
    @patch('stillme_core.learning.pipeline.LearningPipeline')
    def test_new_learning_adapter_init(self, mock_pipeline):
        """Test new learning adapter initialization"""
        adapter = NewLearningAdapter()
        
        mock_pipeline.assert_called_once()
        assert adapter.pipeline is not None
    
    def test_old_learning_adapter_no_import(self):
        """Test old learning adapter when import fails"""
        with patch('stillme_core.core.self_learning.experience_memory.ExperienceMemory', side_effect=ImportError):
            adapter = OldLearningAdapter()
            assert adapter.experience_memory is None
    
    def test_new_learning_adapter_no_import(self):
        """Test new learning adapter when import fails"""
        with patch('stillme_core.learning.pipeline.LearningPipeline', side_effect=ImportError):
            adapter = NewLearningAdapter()
            assert adapter.pipeline is None


class TestGlobalFunctions:
    """Test global functions"""
    
    @patch('stillme_core.learning.unified_learning_manager.UnifiedLearningManager')
    def test_get_unified_learning_manager(self, mock_manager_class):
        """Test getting global unified learning manager"""
        from stillme_core.learning.unified_learning_manager import get_unified_learning_manager
        
        # First call should create instance
        manager1 = get_unified_learning_manager()
        mock_manager_class.assert_called_once()
        
        # Second call should return same instance
        manager2 = get_unified_learning_manager()
        assert manager1 is manager2
    
    @patch('stillme_core.learning.unified_learning_manager.UnifiedLearningManager')
    def test_initialize_learning_systems(self, mock_manager_class):
        """Test initializing learning systems"""
        from stillme_core.learning.unified_learning_manager import initialize_learning_systems
        
        manager = initialize_learning_systems("test_config.toml")
        
        mock_manager_class.assert_called_once_with("test_config.toml")
        assert manager is not None


if __name__ == "__main__":
    pytest.main([__file__])
