"""
Chaos Tests for Phase 4 - Documentation & Debugging
Test khắc nghiệt cho các module Phase 4

Tính năng:
1. Error Injection Tests - Test error injection
2. Long-running Debug Sessions - Test debug sessions dài
3. Memory Stress Tests - Test memory stress
4. Concurrent Access Tests - Test concurrent access
5. Data Corruption Tests - Test data corruption handling
"""

import pytest
import sys
import os
import time
import threading
import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add agent-dev path to sys.path
agent_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agent-dev', 'core')
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures

class TestDocumentationGeneratorChaos:
    """Chaos tests for Documentation Generator"""
    
    def test_documentation_generator_memory_stress(self):
        """Test memory stress with large files"""
        try:
            from documentation_generator import DocumentationGenerator
            
            temp_project = TestFixtures.create_temp_project()
            generator = DocumentationGenerator(str(temp_project))
            
            # Create large Python file to stress test
            large_content = '''
def function_1():
    """Function 1"""
    pass

def function_2():
    """Function 2"""
    pass

class LargeClass:
    """Large class with many methods"""
    
    def method_1(self):
        pass
    
    def method_2(self):
        pass
''' * 100  # Repeat 100 times
            
            large_file = temp_project / "large_file.py"
            with open(large_file, 'w', encoding='utf-8') as f:
                f.write(large_content)
            
            # Test memory stress
            start_time = time.time()
            report = generator.generate_documentation_report()
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 30, f"Memory stress test took {end_time - start_time}s"
            assert report is not None
            assert report.total_files > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("DocumentationGenerator not available")
    
    def test_documentation_generator_concurrent_access(self):
        """Test concurrent access to documentation generator"""
        try:
            from documentation_generator import DocumentationGenerator
            
            temp_project = TestFixtures.create_temp_project()
            generator = DocumentationGenerator(str(temp_project))
            
            results = []
            errors = []
            
            def worker(worker_id):
                try:
                    # Create test file
                    test_file = temp_project / f"test_file_{worker_id}.py"
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(f'''
def function_{worker_id}():
    """Function {worker_id}"""
    return {worker_id}
''')
                    
                    # Generate documentation
                    doc = generator.generate_module_documentation(str(test_file))
                    results.append(doc)
                except Exception as e:
                    errors.append(e)
            
            # Start multiple threads
            threads = []
            for i in range(10):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Should have results from all threads
            assert len(results) == 10, f"Expected 10 results, got {len(results)}"
            assert len(errors) == 0, f"Errors occurred: {errors}"
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("DocumentationGenerator not available")
    
    def test_documentation_generator_error_injection(self):
        """Test error injection scenarios"""
        try:
            from documentation_generator import DocumentationGenerator
            
            temp_project = TestFixtures.create_temp_project()
            generator = DocumentationGenerator(str(temp_project))
            
            # Test with corrupted file
            corrupted_file = temp_project / "corrupted.py"
            with open(corrupted_file, 'w', encoding='utf-8') as f:
                f.write("invalid python syntax {")
            
            # Should handle gracefully
            doc = generator.generate_module_documentation(str(corrupted_file))
            assert doc is not None
            assert doc.quality_score == 0.0  # Should have low quality score
            
            # Test with non-existent file
            non_existent = temp_project / "non_existent.py"
            doc = generator.generate_module_documentation(str(non_existent))
            assert doc is not None
            
            # Test with empty file
            empty_file = temp_project / "empty.py"
            empty_file.touch()
            doc = generator.generate_module_documentation(str(empty_file))
            assert doc is not None
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("DocumentationGenerator not available")
    
    def test_documentation_generator_data_corruption(self):
        """Test data corruption handling"""
        try:
            from documentation_generator import DocumentationGenerator
            
            temp_project = TestFixtures.create_temp_project()
            generator = DocumentationGenerator(str(temp_project))
            
            # Create file with corrupted encoding
            corrupted_file = temp_project / "corrupted_encoding.py"
            with open(corrupted_file, 'w', encoding='utf-8') as f:
                f.write("def test(): pass")
            
            # Corrupt the file
            with open(corrupted_file, 'wb') as f:
                f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            
            # Should handle gracefully
            try:
                doc = generator.generate_module_documentation(str(corrupted_file))
                assert doc is not None
            except UnicodeDecodeError:
                # Expected for corrupted encoding
                pass
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("DocumentationGenerator not available")

class TestDebuggingSystemChaos:
    """Chaos tests for Advanced Debugging System"""
    
    def test_debugging_system_long_running_sessions(self):
        """Test long-running debug sessions"""
        try:
            from debugging_system import AdvancedDebuggingSystem, DebugLevel
            
            temp_project = TestFixtures.create_temp_project()
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            # Start long-running session
            session_id = debug_system.start_debug_session("Long Running Test")
            
            # Simulate long-running session with many logs
            for i in range(1000):
                debug_system.log_debug_event(
                    DebugLevel.INFO,
                    f"Long running test message {i}",
                    "test_module",
                    "test_function",
                    i,
                    session_id
                )
                
                if i % 100 == 0:
                    time.sleep(0.001)  # Small delay every 100 messages
            
            # End session
            session = debug_system.end_debug_session(session_id, "Long running test completed")
            
            # Verify session data
            assert session.error_count == 0
            assert session.warnings_count == 0
            assert len(session.logs) == 1000
            assert session.duration is not None
            assert session.duration > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AdvancedDebuggingSystem not available")
    
    def test_debugging_system_error_injection(self):
        """Test error injection in debugging system"""
        try:
            from debugging_system import AdvancedDebuggingSystem, DebugLevel, ErrorType
            
            temp_project = TestFixtures.create_temp_project()
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            session_id = debug_system.start_debug_session("Error Injection Test")
            
            # Inject various error types
            error_messages = [
                "SyntaxError: invalid syntax",
                "ImportError: No module named 'nonexistent'",
                "AttributeError: 'NoneType' object has no attribute 'method'",
                "KeyError: 'missing_key'",
                "TimeoutError: operation timed out",
                "MemoryError: out of memory"
            ]
            
            for error_msg in error_messages:
                debug_system.log_debug_event(
                    DebugLevel.ERROR,
                    error_msg,
                    "test_module",
                    "test_function",
                    1,
                    session_id
                )
            
            # End session
            session = debug_system.end_debug_session(session_id, "Error injection test completed")
            
            # Verify error patterns were detected
            assert session.error_count == len(error_messages)
            assert len(session.error_patterns) > 0
            
            # Analyze root cause
            analysis = debug_system.analyze_root_cause(session_id)
            assert analysis is not None
            assert len(analysis.error_patterns) > 0
            assert len(analysis.recommendations) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AdvancedDebuggingSystem not available")
    
    def test_debugging_system_concurrent_sessions(self):
        """Test concurrent debug sessions"""
        try:
            from debugging_system import AdvancedDebuggingSystem, DebugLevel
            
            temp_project = TestFixtures.create_temp_project()
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            sessions = []
            errors = []
            
            def worker(worker_id):
                try:
                    session_id = debug_system.start_debug_session(f"Concurrent Session {worker_id}")
                    
                    # Log some events
                    for i in range(10):
                        debug_system.log_debug_event(
                            DebugLevel.INFO,
                            f"Worker {worker_id} message {i}",
                            f"worker_{worker_id}",
                            "test_function",
                            i,
                            session_id
                        )
                    
                    # End session
                    session = debug_system.end_debug_session(session_id, f"Worker {worker_id} completed")
                    sessions.append(session)
                except Exception as e:
                    errors.append(e)
            
            # Start multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify all sessions completed
            assert len(sessions) == 5, f"Expected 5 sessions, got {len(sessions)}"
            assert len(errors) == 0, f"Errors occurred: {errors}"
            
            # Verify session data
            for session in sessions:
                assert session.status.value == "completed"
                assert len(session.logs) == 10
                assert session.duration is not None
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AdvancedDebuggingSystem not available")
    
    def test_debugging_system_memory_stress(self):
        """Test memory stress with many sessions and logs"""
        try:
            from debugging_system import AdvancedDebuggingSystem, DebugLevel
            
            temp_project = TestFixtures.create_temp_project()
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            # Create many sessions with many logs
            session_ids = []
            for i in range(50):  # 50 sessions
                session_id = debug_system.start_debug_session(f"Memory Stress Session {i}")
                session_ids.append(session_id)
                
                # Add many logs to each session
                for j in range(100):  # 100 logs per session
                    debug_system.log_debug_event(
                        DebugLevel.INFO,
                        f"Memory stress test {i}-{j}",
                        f"stress_module_{i}",
                        "stress_function",
                        j,
                        session_id
                    )
            
            # End all sessions
            for session_id in session_ids:
                debug_system.end_debug_session(session_id, "Memory stress test completed")
            
            # Generate report
            report = debug_system.generate_debugging_report()
            assert report is not None
            assert report.total_sessions >= 50
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AdvancedDebuggingSystem not available")
    
    def test_debugging_system_data_corruption(self):
        """Test data corruption handling"""
        try:
            from debugging_system import AdvancedDebuggingSystem, DebugLevel
            
            temp_project = TestFixtures.create_temp_project()
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            session_id = debug_system.start_debug_session("Data Corruption Test")
            
            # Log with corrupted data
            corrupted_messages = [
                "Normal message",
                "Message with null bytes\x00\x00",
                "Message with unicode issues\xff\xfe",
                "Very long message " * 1000,
                "",  # Empty message
                "Message with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
            ]
            
            for msg in corrupted_messages:
                debug_system.log_debug_event(
                    DebugLevel.INFO,
                    msg,
                    "corruption_test",
                    "test_function",
                    1,
                    session_id
                )
            
            # End session
            session = debug_system.end_debug_session(session_id, "Data corruption test completed")
            
            # Should handle all messages gracefully
            assert len(session.logs) == len(corrupted_messages)
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AdvancedDebuggingSystem not available")

class TestPhase4IntegrationChaos:
    """Integration chaos tests for Phase 4 modules"""
    
    def test_phase4_modules_integration_chaos(self):
        """Test integration between Phase 4 modules under chaos conditions"""
        try:
            from documentation_generator import DocumentationGenerator
            from debugging_system import AdvancedDebuggingSystem, DebugLevel
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize both systems
            doc_generator = DocumentationGenerator(str(temp_project))
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            # Start debug session
            session_id = debug_system.start_debug_session("Phase 4 Integration Chaos")
            
            # Create test files while logging debug events
            for i in range(10):
                test_file = temp_project / f"chaos_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
def chaos_function_{i}():
    """Chaos test function {i}"""
    return {i}

class ChaosClass_{i}:
    """Chaos test class {i}"""
    pass
''')
                
                # Log debug event
                debug_system.log_debug_event(
                    DebugLevel.INFO,
                    f"Created chaos test file {i}",
                    "chaos_integration",
                    "create_test_file",
                    i,
                    session_id
                )
            
            # Generate documentation while debug session is active
            doc_report = doc_generator.generate_documentation_report()
            
            # Log documentation generation
            debug_system.log_debug_event(
                DebugLevel.INFO,
                f"Generated documentation for {doc_report.total_files} files",
                "chaos_integration",
                "generate_docs",
                1,
                session_id
            )
            
            # End debug session
            session = debug_system.end_debug_session(session_id, "Phase 4 integration chaos completed")
            
            # Verify integration worked
            assert doc_report is not None
            assert doc_report.total_files >= 10
            assert session is not None
            assert len(session.logs) >= 11  # 10 file creation + 1 doc generation
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 4 modules not available")
    
    def test_phase4_performance_under_chaos(self):
        """Test performance of Phase 4 modules under chaos conditions"""
        try:
            from documentation_generator import DocumentationGenerator
            from debugging_system import AdvancedDebuggingSystem, DebugLevel
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize systems
            doc_generator = DocumentationGenerator(str(temp_project))
            debug_system = AdvancedDebuggingSystem(str(temp_project))
            
            # Start performance test
            start_time = time.time()
            
            # Create many files and sessions simultaneously
            session_ids = []
            for i in range(20):
                # Create test file
                test_file = temp_project / f"perf_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f"def perf_function_{i}(): return {i}")
                
                # Start debug session
                session_id = debug_system.start_debug_session(f"Performance Session {i}")
                session_ids.append(session_id)
                
                # Log events
                debug_system.log_debug_event(
                    DebugLevel.INFO,
                    f"Performance test {i}",
                    "perf_test",
                    "test_function",
                    i,
                    session_id
                )
            
            # Generate documentation
            doc_report = doc_generator.generate_documentation_report()
            
            # End all sessions
            for session_id in session_ids:
                debug_system.end_debug_session(session_id, "Performance test completed")
            
            # Generate debugging report
            debug_report = debug_system.generate_debugging_report()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete within reasonable time
            assert total_time < 60, f"Performance test took {total_time}s"
            assert doc_report is not None
            assert debug_report is not None
            assert debug_report.total_sessions >= 20
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 4 modules not available")
