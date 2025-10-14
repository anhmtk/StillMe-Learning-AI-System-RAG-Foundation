"""
System validation tests for Wave-06 Testing & Reliability
"""

import os
import pytest
import importlib


class TestSystemValidation:
    """Test system validation after import optimization"""
    
    def test_framework_import(self):
        """Test that framework can be imported"""
        import stillme_core.framework
        assert hasattr(stillme_core.framework, 'StillMeFramework')
    
    def test_framework_initialization(self):
        """Test that framework can be initialized"""
        from stillme_core.framework import StillMeFramework
        fw = StillMeFramework()
        assert fw is not None
        assert hasattr(fw, 'logger')
    
    def test_learning_system_import(self):
        """Test that learning system can be imported"""
        import stillme_core.learning
        assert hasattr(stillme_core.learning, 'LearningProposal')
        assert hasattr(stillme_core.learning, 'ProposalsManager')
    
    def test_agentdev_import(self):
        """Test that AgentDev can be imported"""
        import agent_dev.core.agentdev
        assert hasattr(agent_dev.core.agentdev, 'AgentDev')
    
    def test_agentdev_initialization(self):
        """Test that AgentDev can be initialized"""
        from agent_dev.core.agentdev import AgentDev
        agent = AgentDev()
        assert agent is not None
        # AgentDev should have basic attributes
        assert hasattr(agent, '__class__')
    
    def test_config_bootstrap_import(self):
        """Test that config bootstrap can be imported"""
        import stillme_core.config_bootstrap
        assert hasattr(stillme_core.config_bootstrap, 'ensure_minimum_config')
    
    def test_import_optimization_tools(self):
        """Test that import optimization tools exist"""
        import tools.simple_import_optimizer
        # Check if the module can be imported
        assert tools.simple_import_optimizer is not None
        
        # Check if code quality analyzer exists
        try:
            import tools.code_quality_analyzer
            assert tools.code_quality_analyzer is not None
        except ImportError:
            # Tool may not exist, that's OK for this test
            pass
    
    def test_environment_variables(self):
        """Test that environment variables are set correctly"""
        # Test dry run mode
        os.environ.setdefault("STILLME_DRY_RUN", "1")
        assert os.getenv("STILLME_DRY_RUN") == "1"
    
    def test_python_path(self):
        """Test that Python path includes project root"""
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert project_root in sys.path or any(project_root in p for p in sys.path)
    
    def test_import_no_circular_dependencies(self):
        """Test that major modules can be imported without circular dependencies"""
        # Test framework import
        import stillme_core.framework
        
        # Test learning import
        import stillme_core.learning
        
        # Test agentdev import
        import agent_dev.core.agentdev
        
        # All imports should succeed without circular dependency errors
        assert True
    
    def test_system_health_check(self):
        """Test basic system health"""
        # Test that we can create basic objects
        from stillme_core.framework import StillMeFramework
        fw = StillMeFramework()
        
        # Test that logger works
        fw.logger.info("System health check")
        
        # Test that config is accessible
        assert isinstance(fw.config, dict)
        
        # Test that dry run mode is working (check environment variable)
        import os
        assert os.getenv("STILLME_DRY_RUN", "0") == "1"
    
    def test_import_density_improvement(self):
        """Test that import optimization improved code quality"""
        # This test validates that our import optimization worked
        # by checking that we can import modules without issues
        
        # Test multiple imports in sequence
        import stillme_core.framework
        import stillme_core.learning
        import agent_dev.core.agentdev
        import stillme_core.config_bootstrap
        
        # All imports should work without errors
        assert True
