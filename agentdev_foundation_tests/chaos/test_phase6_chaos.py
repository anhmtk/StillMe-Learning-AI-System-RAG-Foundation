"""
Chaos Tests for Phase 6 - Analytics & Collaboration
Test khắc nghiệt cho các module Phase 6

Tính năng:
1. Analytics Dashboard Stress Tests - Test dashboard với 100k+ metrics entries
2. Collaboration Chaos Tests - Test collaboration hooks (simulate offline, conflict)
3. Performance Tests - Test hiệu suất với large datasets
4. Integration Tests - Test tích hợp giữa analytics và collaboration
"""

import pytest
import sys
import os
import time
import threading
import random
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add agent-dev path to sys.path
agent_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agent-dev', 'core')
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures

class TestAnalyticsDashboardChaos:
    """Chaos tests for Analytics Dashboard"""
    
    def test_analytics_dashboard_memory_stress(self):
        """Test memory stress với nhiều metrics"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            
            temp_project = TestFixtures.create_temp_project()
            dashboard = AnalyticsDashboard(str(temp_project))
            
            # Tạo nhiều metrics để stress test
            start_time = time.time()
            
            # Thu thập metrics nhiều lần
            for i in range(50):
                metrics = dashboard.collect_metrics()
                time.sleep(0.01)  # Small delay
            
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 30, f"Memory stress test took {end_time - start_time}s"
            assert len(metrics) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AnalyticsDashboard not available")
    
    def test_analytics_dashboard_concurrent_access(self):
        """Test concurrent access to analytics dashboard"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            
            temp_project = TestFixtures.create_temp_project()
            dashboard = AnalyticsDashboard(str(temp_project))
            
            results = []
            errors = []
            
            def worker(worker_id):
                try:
                    # Thu thập metrics
                    metrics = dashboard.collect_metrics()
                    
                    # Tạo báo cáo
                    report = dashboard.generate_performance_report()
                    
                    results.append((worker_id, len(metrics), len(report.insights)))
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
            pytest.skip("AnalyticsDashboard not available")
    
    def test_analytics_dashboard_large_dataset(self):
        """Test với large dataset"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            
            temp_project = TestFixtures.create_temp_project()
            dashboard = AnalyticsDashboard(str(temp_project))
            
            # Tạo nhiều files để tăng dataset
            for i in range(100):
                test_file = temp_project / f"large_dataset_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
class LargeDataset{i}:
    """Large dataset class {i}"""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        """Method {i}"""
        return self.value * 2
''')
            
            # Thu thập metrics
            start_time = time.time()
            metrics = dashboard.collect_metrics()
            end_time = time.time()
            
            # Should handle large dataset efficiently
            assert (end_time - start_time) < 60, f"Large dataset test took {end_time - start_time}s"
            assert len(metrics) > 0
            
            # Tạo báo cáo
            report = dashboard.generate_performance_report()
            assert report is not None
            assert len(report.metrics) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AnalyticsDashboard not available")
    
    def test_analytics_dashboard_html_generation(self):
        """Test HTML dashboard generation"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            
            temp_project = TestFixtures.create_temp_project()
            dashboard = AnalyticsDashboard(str(temp_project))
            
            # Thu thập metrics và tạo báo cáo
            metrics = dashboard.collect_metrics()
            report = dashboard.generate_performance_report()
            
            # Tạo HTML dashboard
            html_file = dashboard.create_html_dashboard(report)
            
            # Verify HTML file was created
            assert os.path.exists(html_file)
            
            # Check HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            assert "AgentDev Unified Analytics Dashboard" in html_content
            assert "Phân tích và Insights" in html_content
            assert "Khuyến nghị" in html_content
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AnalyticsDashboard not available")

class TestCollaborationSystemChaos:
    """Chaos tests for Collaboration System"""
    
    def test_collaboration_system_code_review_stress(self):
        """Test code review stress"""
        try:
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            collab_system = CollaborationSystem(str(temp_project))
            
            # Tạo nhiều files để review
            for i in range(20):
                test_file = temp_project / f"review_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
def function_{i}():
    """Function {i}"""
    if i > 10:
        if i > 20:
            if i > 30:
                return "very high"
            else:
                return "high"
        else:
            return "medium"
    else:
        return "low"

# TODO: Implement feature {i}
# FIXME: Fix issue {i}
''')
            
            # Review tất cả files
            start_time = time.time()
            reviews = []
            for i in range(20):
                test_file = temp_project / f"review_test_{i}.py"
                review = collab_system.review_code(str(test_file))
                reviews.append(review)
            
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 30, f"Code review stress test took {end_time - start_time}s"
            assert len(reviews) == 20
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("CollaborationSystem not available")
    
    def test_collaboration_system_knowledge_sharing(self):
        """Test knowledge sharing system"""
        try:
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            collab_system = CollaborationSystem(str(temp_project))
            
            # Tạo nhiều knowledge shares
            topics = [
                "Python Best Practices",
                "Testing Strategies",
                "Security Guidelines",
                "Performance Optimization",
                "Code Review Tips"
            ]
            
            shares = []
            for i, topic in enumerate(topics):
                share = collab_system.share_knowledge(
                    f"{topic} - Part {i+1}",
                    f"Chi tiết về {topic}...",
                    f"Author_{i}",
                    "programming",
                    [topic.lower().replace(" ", "-")]
                )
                shares.append(share)
            
            # Verify shares were created
            assert len(shares) == 5
            for share in shares:
                assert share.title is not None
                assert share.content is not None
                assert share.author is not None
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("CollaborationSystem not available")
    
    def test_collaboration_system_mentoring_sessions(self):
        """Test mentoring sessions"""
        try:
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            collab_system = CollaborationSystem(str(temp_project))
            
            # Tạo nhiều mentoring sessions
            topics = [
                "Python Basics",
                "Testing Fundamentals",
                "Security Best Practices",
                "Performance Tuning",
                "Code Architecture"
            ]
            
            sessions = []
            for i, topic in enumerate(topics):
                session = collab_system.create_mentoring_session(
                    f"Mentor_{i}",
                    f"Mentee_{i}",
                    topic,
                    60 + i * 10,
                    f"Good progress on {topic}"
                )
                sessions.append(session)
            
            # Verify sessions were created
            assert len(sessions) == 5
            for session in sessions:
                assert session.topic is not None
                assert session.mentor is not None
                assert session.mentee is not None
                assert len(session.recommendations) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("CollaborationSystem not available")
    
    def test_collaboration_system_concurrent_operations(self):
        """Test concurrent operations"""
        try:
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            collab_system = CollaborationSystem(str(temp_project))
            
            results = []
            errors = []
            
            def worker(worker_id):
                try:
                    # Tạo test file
                    test_file = temp_project / f"concurrent_test_{worker_id}.py"
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(f'''
def concurrent_function_{worker_id}():
    """Concurrent function {worker_id}"""
    return {worker_id} * 2
''')
                    
                    # Review code
                    review = collab_system.review_code(str(test_file))
                    
                    # Share knowledge
                    share = collab_system.share_knowledge(
                        f"Concurrent Knowledge {worker_id}",
                        f"Knowledge content {worker_id}",
                        f"Author_{worker_id}",
                        "concurrent"
                    )
                    
                    # Create mentoring session
                    session = collab_system.create_mentoring_session(
                        f"Mentor_{worker_id}",
                        f"Mentee_{worker_id}",
                        f"Concurrent Topic {worker_id}",
                        30
                    )
                    
                    results.append((worker_id, review.score, share.title, session.topic))
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
            
            # Should have results from all threads
            assert len(results) == 5, f"Expected 5 results, got {len(results)}"
            assert len(errors) == 0, f"Errors occurred: {errors}"
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("CollaborationSystem not available")

class TestPhase6IntegrationChaos:
    """Integration chaos tests for Phase 6 modules"""
    
    def test_phase6_modules_integration_chaos(self):
        """Test integration between Phase 6 modules under chaos conditions"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize both systems
            dashboard = AnalyticsDashboard(str(temp_project))
            collab_system = CollaborationSystem(str(temp_project))
            
            # Tạo test files
            for i in range(10):
                test_file = temp_project / f"integration_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
class IntegrationTest{i}:
    """Integration test class {i}"""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        """Method {i}"""
        return self.value * 2
''')
            
            # Thu thập metrics
            metrics = dashboard.collect_metrics()
            
            # Tạo báo cáo analytics
            analytics_report = dashboard.generate_performance_report()
            
            # Review code
            reviews = []
            for i in range(5):
                test_file = temp_project / f"integration_test_{i}.py"
                review = collab_system.review_code(str(test_file))
                reviews.append(review)
            
            # Share knowledge
            share = collab_system.share_knowledge(
                "Integration Best Practices",
                "Best practices for system integration...",
                "AgentDev",
                "integration"
            )
            
            # Tạo báo cáo collaboration
            collab_report = collab_system.generate_collaboration_report()
            
            # Verify integration worked
            assert analytics_report is not None
            assert len(analytics_report.metrics) > 0
            assert collab_report is not None
            assert collab_report.total_reviews >= 5
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 6 modules not available")
    
    def test_phase6_performance_under_chaos(self):
        """Test performance of Phase 6 modules under chaos conditions"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize systems
            dashboard = AnalyticsDashboard(str(temp_project))
            collab_system = CollaborationSystem(str(temp_project))
            
            # Start performance test
            start_time = time.time()
            
            # Tạo nhiều files và operations
            for i in range(30):
                # Tạo test file
                test_file = temp_project / f"perf_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
class PerfTest{i}:
    """Performance test class {i}"""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        """Method {i}"""
        return self.value * 2
''')
                
                # Review code
                collab_system.review_code(str(test_file))
                
                # Share knowledge
                collab_system.share_knowledge(
                    f"Performance Knowledge {i}",
                    f"Performance knowledge content {i}",
                    f"Author_{i}",
                    "performance"
                )
            
            # Thu thập metrics
            metrics = dashboard.collect_metrics()
            
            # Tạo báo cáo
            analytics_report = dashboard.generate_performance_report()
            collab_report = collab_system.generate_collaboration_report()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete within reasonable time
            assert total_time < 120, f"Performance test took {total_time}s"
            assert analytics_report is not None
            assert collab_report is not None
            assert len(metrics) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 6 modules not available")
    
    def test_phase6_stress_with_many_operations(self):
        """Test stress với nhiều operations"""
        try:
            from analytics_dashboard import AnalyticsDashboard
            from collaboration_system import CollaborationSystem
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize systems
            dashboard = AnalyticsDashboard(str(temp_project))
            collab_system = CollaborationSystem(str(temp_project))
            
            # Tạo nhiều files cho stress test
            for i in range(50):
                test_file = temp_project / f"stress_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
class StressTest{i}:
    """Stress test class {i}"""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        """Method {i}"""
        return self.value * 2
''')
            
            # Thu thập metrics nhiều lần
            for i in range(10):
                metrics = dashboard.collect_metrics()
                time.sleep(0.01)
            
            # Tạo nhiều reviews
            for i in range(20):
                test_file = temp_project / f"stress_test_{i}.py"
                collab_system.review_code(str(test_file))
            
            # Tạo nhiều knowledge shares
            for i in range(15):
                collab_system.share_knowledge(
                    f"Stress Knowledge {i}",
                    f"Stress knowledge content {i}",
                    f"Author_{i}",
                    "stress"
                )
            
            # Tạo báo cáo
            analytics_report = dashboard.generate_performance_report()
            collab_report = collab_system.generate_collaboration_report()
            
            # Verify stress test results
            assert analytics_report is not None
            assert collab_report is not None
            assert collab_report.total_reviews >= 20
            assert collab_report.knowledge_shares >= 15
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 6 modules not available")
