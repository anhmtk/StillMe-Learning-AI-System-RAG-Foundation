"""
Tests for Daily Supervisor flow
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from stillme_core.supervisor import DailySupervisor, LessonProposal, KnowledgePack


class TestSupervisorFlow:
    def test_collect_signals(self, tmp_path):
        """Test signal collection"""
        supervisor = DailySupervisor(repo_root=str(tmp_path))
        
        # Create mock AgentDev log
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        agentdev_log = logs_dir / "agentdev.jsonl"
        
        log_entry = {
            "timestamp": "2025-09-06T14:50:00",
            "step_id": 1,
            "action": "test_action",
            "ok": False,
            "duration_s": 1.5,
            "stdout_tail": "Test error",
            "description": "Test step"
        }
        
        with open(agentdev_log, 'w') as f:
            f.write(json.dumps(log_entry) + "\n")
        
        signals = supervisor.collect_signals()
        
        assert "timestamp" in signals
        assert len(signals["agentdev_logs"]) == 1
        assert signals["agentdev_logs"][0]["action"] == "test_action"
        assert len(signals["error_patterns"]) == 1
        assert signals["error_patterns"][0]["action"] == "test_action"
    
    def test_propose_lessons(self, tmp_path):
        """Test lesson proposal generation"""
        supervisor = DailySupervisor(repo_root=str(tmp_path))
        
        signals = {
            "timestamp": "2025-09-06T14:50:00",
            "agentdev_logs": [
                {
                    "action": "test_action",
                    "ok": False,
                    "stdout_tail": "Test error"
                }
            ],
            "memory_usage": {
                "risk_score": 0.8,
                "test_files": ["test_memory.py"]
            },
            "error_patterns": [
                {
                    "action": "test_action",
                    "error": "Test error"
                }
            ]
        }
        
        proposals = supervisor.propose_lessons(signals)
        
        assert len(proposals) >= 2  # Should have memory and error handling proposals
        assert any(p.id == "memory_stability_001" for p in proposals)
        assert any(p.id == "error_handling_001" for p in proposals)
        
        # Check proposal structure
        memory_proposal = next(p for p in proposals if p.id == "memory_stability_001")
        assert memory_proposal.title == "Memory Module Stability Best Practices"
        assert len(memory_proposal.examples) > 0
        assert memory_proposal.safety_notes != ""
    
    def test_save_and_load_proposals(self, tmp_path):
        """Test saving and loading lesson proposals"""
        supervisor = DailySupervisor(repo_root=str(tmp_path))
        
        proposals = [
            LessonProposal(
                id="test_001",
                title="Test Lesson",
                guideline="Test guideline",
                examples=["Example 1", "Example 2"],
                safety_notes="Test safety notes",
                success_criteria="Test success criteria",
                created_at="2025-09-06T14:50:00",
                source="test"
            )
        ]
        
        proposals_file = supervisor.save_lesson_proposals(proposals)
        assert Path(proposals_file).exists()
        
        # Load proposals
        loaded_proposals = supervisor.get_current_proposals()
        assert len(loaded_proposals) == 1
        assert loaded_proposals[0].id == "test_001"
        assert loaded_proposals[0].title == "Test Lesson"
    
    def test_approve_lessons(self, tmp_path):
        """Test lesson approval and knowledge pack creation"""
        supervisor = DailySupervisor(repo_root=str(tmp_path))
        
        # First create proposals
        proposals = [
            LessonProposal(
                id="test_001",
                title="Test Lesson 1",
                guideline="Test guideline 1",
                examples=["Example 1"],
                safety_notes="Test safety notes 1",
                success_criteria="Test success criteria 1",
                created_at="2025-09-06T14:50:00",
                source="test"
            ),
            LessonProposal(
                id="test_002",
                title="Test Lesson 2",
                guideline="Test guideline 2",
                examples=["Example 2"],
                safety_notes="Test safety notes 2",
                success_criteria="Test success criteria 2",
                created_at="2025-09-06T14:50:00",
                source="test"
            )
        ]
        
        supervisor.save_lesson_proposals(proposals)
        
        # Approve one lesson
        knowledge_pack = supervisor.approve_lessons(["test_001"])
        
        assert knowledge_pack.id.startswith("pack_")
        assert knowledge_pack.version == "1.0"
        assert len(knowledge_pack.lessons) == 1
        assert knowledge_pack.lessons[0].id == "test_001"
        assert "1 approved lessons" in knowledge_pack.summary
        
        # Check that knowledge pack file was created
        pack_files = list((tmp_path / "knowledge_packs").glob("pack_*.json"))
        assert len(pack_files) == 1
    
    def test_get_latest_knowledge_pack(self, tmp_path):
        """Test getting latest knowledge pack"""
        supervisor = DailySupervisor(repo_root=str(tmp_path))
        
        # No knowledge pack initially
        latest_pack = supervisor.get_latest_knowledge_pack()
        assert latest_pack is None
        
        # Create a knowledge pack
        proposals = [
            LessonProposal(
                id="test_001",
                title="Test Lesson",
                guideline="Test guideline",
                examples=["Example 1"],
                safety_notes="Test safety notes",
                success_criteria="Test success criteria",
                created_at="2025-09-06T14:50:00",
                source="test"
            )
        ]
        
        supervisor.save_lesson_proposals(proposals)
        knowledge_pack = supervisor.approve_lessons(["test_001"])
        
        # Get latest pack
        latest_pack = supervisor.get_latest_knowledge_pack()
        assert latest_pack is not None
        assert latest_pack.id == knowledge_pack.id
        assert len(latest_pack.lessons) == 1
