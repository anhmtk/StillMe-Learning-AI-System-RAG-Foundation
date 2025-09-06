"""
Test API bridge endpoints for AgentDev
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api_server import app


class TestAPIBridge:
    def test_health_ai_endpoint(self):
        """Test GET /health/ai endpoint"""
        with TestClient(app) as client:
            response = client.get("/health/ai")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "ok" in data
            assert "details" in data
            assert data["ok"] is True
            
            # Check details structure
            details = data["details"]
            assert "gpt5" in details
            assert "ollama" in details
            assert "agentdev" in details
            
            # Check agentdev component
            assert "ok" in details["agentdev"]

    def test_dev_agent_bridge_endpoint(self):
        """Test POST /dev-agent/bridge endpoint"""
        with TestClient(app) as client:
            # Test with a simple prompt
            payload = {
                "prompt": "Run unit tests",
                "mode": "safe"
            }
            
            with patch('stillme_core.controller.AgentController') as mock_controller_class:
                mock_controller = Mock()
                mock_controller.run_agent.return_value = {
                    "summary": "AgentDev completed for goal 'Run unit tests'",
                    "pass_rate": 0.8,
                    "steps": [
                        {
                            "id": 1,
                            "desc": "Run tests",
                            "action": "run_tests",
                            "exec_ok": True,
                            "stdout_tail": "1 passed",
                            "duration_s": 2.5
                        },
                        {
                            "id": 2,
                            "desc": "Verify results",
                            "action": "verify",
                            "exec_ok": False,
                            "stdout_tail": "Test failed",
                            "duration_s": 1.0
                        }
                    ],
                    "total_steps": 2,
                    "passed_steps": 1,
                    "total_duration_s": 3.5,
                    "goal": "Run unit tests"
                }
                mock_controller_class.return_value = mock_controller
                
                response = client.post("/dev-agent/bridge", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                
                # Check response structure
                assert "summary" in data
                assert "pass_rate" in data
                assert "steps_tail" in data
                assert "total_steps" in data
                assert "passed_steps" in data
                assert "duration_s" in data
                assert "goal" in data
                
                # Check values
                assert data["pass_rate"] == 0.8
                assert data["total_steps"] == 2
                assert data["passed_steps"] == 1
                assert data["duration_s"] == 3.5
                assert data["goal"] == "Run unit tests"
                assert len(data["steps_tail"]) == 2  # Last 2 steps
                
                # Verify controller was called correctly
                mock_controller.run_agent.assert_called_once_with(goal="Run unit tests", max_steps=3)

    def test_dev_agent_bridge_with_different_prompt(self):
        """Test POST /dev-agent/bridge with different prompt"""
        with TestClient(app) as client:
            payload = {
                "prompt": "Fix failing tests",
                "mode": "fast"
            }
            
            with patch('stillme_core.controller.AgentController') as mock_controller_class:
                mock_controller = Mock()
                mock_controller.run_agent.return_value = {
                    "summary": "AgentDev completed for goal 'Fix failing tests'",
                    "pass_rate": 1.0,
                    "steps": [
                        {
                            "id": 1,
                            "desc": "Fix test",
                            "action": "fix_test",
                            "exec_ok": True,
                            "stdout_tail": "Test fixed",
                            "duration_s": 1.5
                        }
                    ],
                    "total_steps": 1,
                    "passed_steps": 1,
                    "total_duration_s": 1.5,
                    "goal": "Fix failing tests"
                }
                mock_controller_class.return_value = mock_controller
                
                response = client.post("/dev-agent/bridge", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["pass_rate"] == 1.0
                assert data["total_steps"] == 1
                assert data["passed_steps"] == 1
                assert data["goal"] == "Fix failing tests"
                
                # Verify controller was called with correct goal
                mock_controller.run_agent.assert_called_once_with(goal="Fix failing tests", max_steps=3)

    def test_dev_agent_bridge_controller_unavailable(self):
        """Test POST /dev-agent/bridge when controller is unavailable"""
        with TestClient(app) as client:
            payload = {
                "prompt": "Run unit tests",
                "mode": "safe"
            }
            
            with patch('api_server.AgentController', side_effect=ImportError("Module not found")):
                response = client.post("/dev-agent/bridge", json=payload)
                
                assert response.status_code == 503
                data = response.json()
                assert "AgentDev unavailable" in data["detail"]

    def test_dev_agent_bridge_execution_error(self):
        """Test POST /dev-agent/bridge when execution fails"""
        with TestClient(app) as client:
            payload = {
                "prompt": "Run unit tests",
                "mode": "safe"
            }
            
            with patch('stillme_core.controller.AgentController') as mock_controller_class:
                mock_controller = Mock()
                mock_controller.run_agent.side_effect = Exception("Execution failed")
                mock_controller_class.return_value = mock_controller
                
                response = client.post("/dev-agent/bridge", json=payload)
                
                assert response.status_code == 500
                data = response.json()
                assert "AgentDev execution failed" in data["detail"]

    def test_dev_agent_bridge_minimal_payload(self):
        """Test POST /dev-agent/bridge with minimal payload"""
        with TestClient(app) as client:
            payload = {
                "prompt": "Test"
            }
            
            with patch('stillme_core.controller.AgentController') as mock_controller_class:
                mock_controller = Mock()
                mock_controller.run_agent.return_value = {
                    "summary": "AgentDev completed",
                    "pass_rate": 0.0,
                    "steps": [],
                    "total_steps": 0,
                    "passed_steps": 0,
                    "total_duration_s": 0.0,
                    "goal": "Test"
                }
                mock_controller_class.return_value = mock_controller
                
                response = client.post("/dev-agent/bridge", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["pass_rate"] == 0.0
                assert data["total_steps"] == 0
                assert data["passed_steps"] == 0
                assert data["goal"] == "Test"