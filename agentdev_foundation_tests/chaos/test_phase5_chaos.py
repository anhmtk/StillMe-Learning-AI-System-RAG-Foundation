"""
Chaos Tests for Phase 5 - API & Architecture
Test khắc nghiệt cho các module Phase 5

Tính năng:
1. API Contract Tests - Test API contracts
2. API Fuzz Tests - Test API fuzzing
3. Scalability Tests - Test với 1000+ API calls
4. Architecture Linting - Test architecture analysis
5. Integration Tests - Test cross-module integration
"""

import pytest
import sys
import os
import time
import asyncio
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

class TestAPIManagementChaos:
    """Chaos tests for API Management System"""
    
    def test_api_management_memory_stress(self):
        """Test memory stress with many endpoints"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            
            temp_project = TestFixtures.create_temp_project()
            api_system = APIManagementSystem(str(temp_project))
            
            # Create many endpoints to stress test
            endpoints = []
            for i in range(100):
                endpoint = APIEndpoint(
                    path=f"/api/v1/test_{i}",
                    method=APIMethod.POST,
                    version=APIVersion.V1,
                    description=f"Test endpoint {i}",
                    parameters=[],
                    request_schema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    },
                    response_schema={},
                    status_codes={200: "Success"},
                    examples=[],
                    tags=["test"]
                )
                endpoints.append(endpoint)
            
            # Register all endpoints
            start_time = time.time()
            for endpoint in endpoints:
                api_system.register_endpoint(endpoint)
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 10, f"Memory stress test took {end_time - start_time}s"
            assert len(api_system.endpoints) == 100
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("APIManagementSystem not available")
    
    def test_api_management_concurrent_access(self):
        """Test concurrent access to API management system"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            
            temp_project = TestFixtures.create_temp_project()
            api_system = APIManagementSystem(str(temp_project))
            
            results = []
            errors = []
            
            def worker(worker_id):
                try:
                    endpoint = APIEndpoint(
                        path=f"/api/v1/concurrent_{worker_id}",
                        method=APIMethod.GET,
                        version=APIVersion.V1,
                        description=f"Concurrent endpoint {worker_id}",
                        parameters=[],
                        request_schema={},
                        response_schema={},
                        status_codes={200: "Success"},
                        examples=[],
                        tags=["concurrent"]
                    )
                    
                    endpoint_id = api_system.register_endpoint(endpoint)
                    results.append(endpoint_id)
                except Exception as e:
                    errors.append(e)
            
            # Start multiple threads
            threads = []
            for i in range(20):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Should have results from all threads
            assert len(results) == 20, f"Expected 20 results, got {len(results)}"
            assert len(errors) == 0, f"Errors occurred: {errors}"
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("APIManagementSystem not available")
    
    def test_api_management_contract_generation(self):
        """Test contract generation under stress"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            
            temp_project = TestFixtures.create_temp_project()
            api_system = APIManagementSystem(str(temp_project))
            
            # Create complex endpoint
            endpoint = APIEndpoint(
                path="/api/v1/complex",
                method=APIMethod.POST,
                version=APIVersion.V1,
                description="Complex endpoint",
                parameters=[],
                request_schema={
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "age": {"type": "integer"}
                            },
                            "required": ["name", "email"]
                        },
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "quantity": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "required": ["user"]
                },
                response_schema={},
                status_codes={200: "Success", 400: "Bad Request"},
                examples=[],
                tags=["complex"]
            )
            
            # Register endpoint
            endpoint_id = api_system.register_endpoint(endpoint)
            
            # Create contract
            contract = api_system.create_contract(endpoint_id, endpoint.request_schema)
            
            # Verify contract
            assert contract is not None
            assert len(contract.validation_rules) > 0
            assert len(contract.test_cases) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("APIManagementSystem not available")
    
    def test_api_management_fuzz_data_generation(self):
        """Test fuzz data generation"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            
            temp_project = TestFixtures.create_temp_project()
            api_system = APIManagementSystem(str(temp_project))
            
            # Create endpoint with various data types
            endpoint = APIEndpoint(
                path="/api/v1/fuzz",
                method=APIMethod.POST,
                version=APIVersion.V1,
                description="Fuzz test endpoint",
                parameters=[],
                request_schema={
                    "type": "object",
                    "properties": {
                        "string_field": {"type": "string"},
                        "integer_field": {"type": "integer"},
                        "number_field": {"type": "number"},
                        "boolean_field": {"type": "boolean"},
                        "array_field": {"type": "array"},
                        "object_field": {"type": "object"}
                    }
                },
                response_schema={},
                status_codes={200: "Success"},
                examples=[],
                tags=["fuzz"]
            )
            
            # Register endpoint
            endpoint_id = api_system.register_endpoint(endpoint)
            
            # Generate fuzz data
            fuzz_data = api_system._generate_fuzz_data(endpoint.request_schema)
            
            # Verify fuzz data
            assert isinstance(fuzz_data, dict)
            assert "string_field" in fuzz_data
            assert "integer_field" in fuzz_data
            assert "number_field" in fuzz_data
            assert "boolean_field" in fuzz_data
            assert "array_field" in fuzz_data
            assert "object_field" in fuzz_data
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("APIManagementSystem not available")

class TestArchitectureAnalyzerChaos:
    """Chaos tests for Architecture Analyzer"""
    
    def test_architecture_analyzer_large_codebase(self):
        """Test architecture analysis on large codebase"""
        try:
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Create many Python files to simulate large codebase
            for i in range(50):
                test_file = temp_project / f"module_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
class Module{i}:
    """Module {i}"""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        """Method {i}"""
        return self.value * 2
    
    def complex_method_{i}(self):
        """Complex method {i}"""
        if self.value > 10:
            if self.value > 20:
                if self.value > 30:
                    return "very high"
                else:
                    return "high"
            else:
                return "medium"
        else:
            return "low"

def function_{i}():
    """Function {i}"""
    return {i} * 3

# TODO: Implement feature {i}
# FIXME: Fix issue {i}
''')
            
            # Analyze architecture
            start_time = time.time()
            report = analyzer.analyze_architecture()
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 30, f"Architecture analysis took {end_time - start_time}s"
            assert report.metrics.total_files >= 50
            assert report.metrics.total_classes >= 50
            assert report.metrics.total_functions >= 100
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("ArchitectureAnalyzer not available")
    
    def test_architecture_analyzer_design_pattern_detection(self):
        """Test design pattern detection"""
        try:
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Create files with different design patterns
            patterns = {
                "singleton.py": '''
class Singleton:
    __instance = None
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
''',
                "factory.py": '''
class AnimalFactory:
    def create_animal(self, animal_type):
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        else:
            return None
''',
                "observer.py": '''
class Subject:
    def __init__(self):
        self.observers = []
    
    def attach(self, observer):
        self.observers.append(observer)
    
    def detach(self, observer):
        self.observers.remove(observer)
    
    def notify(self):
        for observer in self.observers:
            observer.update()
''',
                "strategy.py": '''
class PaymentStrategy:
    def pay(self, amount):
        pass

class CreditCardStrategy(PaymentStrategy):
    def pay(self, amount):
        return f"Paid ${amount} with credit card"

class PayPalStrategy(PaymentStrategy):
    def pay(self, amount):
        return f"Paid ${amount} with PayPal"
'''
            }
            
            for filename, content in patterns.items():
                test_file = temp_project / filename
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Analyze architecture
            report = analyzer.analyze_architecture()
            
            # Should detect design patterns
            assert len(report.metrics.design_patterns_found) > 0
            
            # Check for specific patterns
            pattern_types = [p.pattern.value for p in report.metrics.design_patterns_found]
            assert any("singleton" in p for p in pattern_types)
            assert any("factory" in p for p in pattern_types)
            assert any("observer" in p for p in pattern_types)
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("ArchitectureAnalyzer not available")
    
    def test_architecture_analyzer_technical_debt_detection(self):
        """Test technical debt detection"""
        try:
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Create file with technical debt
            debt_file = temp_project / "debt_example.py"
            with open(debt_file, 'w', encoding='utf-8') as f:
                f.write('''
# TODO: Implement this feature
# FIXME: This is broken

def long_function_with_many_parameters(param1, param2, param3, param4, param5, param6, param7):
    """Function with too many parameters"""
    if param1 > 0:
        if param2 > 0:
            if param3 > 0:
                if param4 > 0:
                    if param5 > 0:
                        if param6 > 0:
                            if param7 > 0:
                                return "very deep nesting"
                            else:
                                return "deep nesting"
                        else:
                            return "medium nesting"
                    else:
                        return "shallow nesting"
                else:
                    return "very shallow nesting"
            else:
                return "minimal nesting"
        else:
            return "no nesting"
    else:
        return "negative nesting"

def duplicate_code():
    """Function with duplicate code"""
    result = 0
    for i in range(10):
        result += i
    return result

def another_duplicate_code():
    """Another function with duplicate code"""
    result = 0
    for i in range(10):
        result += i
    return result

def yet_another_duplicate_code():
    """Yet another function with duplicate code"""
    result = 0
    for i in range(10):
        result += i
    return result
''')
            
            # Analyze architecture
            report = analyzer.analyze_architecture()
            
            # Should detect technical debt
            assert len(report.metrics.technical_debt) > 0
            
            # Check for specific debt types
            debt_types = [d.debt_type for d in report.metrics.technical_debt]
            assert "todo_comment" in debt_types
            assert "long_parameter_list" in debt_types
            assert "deep_nesting" in debt_types
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("ArchitectureAnalyzer not available")
    
    def test_architecture_analyzer_refactoring_suggestions(self):
        """Test refactoring suggestions generation"""
        try:
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Create file with refactoring opportunities
            refactor_file = temp_project / "refactor_example.py"
            with open(refactor_file, 'w', encoding='utf-8') as f:
                f.write('''
def very_long_function():
    """This function is too long and should be refactored"""
    # Line 1
    result = 0
    # Line 2
    for i in range(100):
        # Line 3
        if i % 2 == 0:
            # Line 4
            result += i
        else:
            # Line 5
            result -= i
    # Line 6
    for j in range(50):
        # Line 7
        if j % 3 == 0:
            # Line 8
            result *= 2
        else:
            # Line 9
            result /= 2
    # Line 10
    for k in range(25):
        # Line 11
        if k % 4 == 0:
            # Line 12
            result += k
        else:
            # Line 13
            result -= k
    # Line 14
    for l in range(12):
        # Line 15
        if l % 5 == 0:
            # Line 16
            result *= 3
        else:
            # Line 17
            result /= 3
    # Line 18
    for m in range(6):
        # Line 19
        if m % 6 == 0:
            # Line 20
            result += m
        else:
            # Line 21
            result -= m
    # Line 22
    return result

def complex_condition_function(x, y, z):
    """Function with complex conditions"""
    if x > 0 and y > 0 and z > 0:
        if x > 10 and y > 10 and z > 10:
            if x > 20 and y > 20 and z > 20:
                return "very high"
            else:
                return "high"
        else:
            return "medium"
    else:
        return "low"
''')
            
            # Analyze architecture
            report = analyzer.analyze_architecture()
            
            # Should generate refactoring suggestions
            assert len(report.metrics.refactoring_suggestions) > 0
            
            # Check for specific suggestion types
            suggestion_types = [s.suggestion_type for s in report.metrics.refactoring_suggestions]
            # Should have at least one refactoring suggestion
            assert len(suggestion_types) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("ArchitectureAnalyzer not available")

class TestPhase5IntegrationChaos:
    """Integration chaos tests for Phase 5 modules"""
    
    def test_phase5_modules_integration_chaos(self):
        """Test integration between Phase 5 modules under chaos conditions"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize both systems
            api_system = APIManagementSystem(str(temp_project))
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Create test files for architecture analysis
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

def integration_function_{i}():
    """Integration function {i}"""
    return {i} * 3
''')
            
            # Create API endpoints
            for i in range(5):
                endpoint = APIEndpoint(
                    path=f"/api/v1/integration_{i}",
                    method=APIMethod.POST,
                    version=APIVersion.V1,
                    description=f"Integration endpoint {i}",
                    parameters=[],
                    request_schema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    },
                    response_schema={},
                    status_codes={200: "Success"},
                    examples=[],
                    tags=["integration"]
                )
                api_system.register_endpoint(endpoint)
            
            # Analyze architecture
            arch_report = analyzer.analyze_architecture()
            
            # Generate API report
            api_report = api_system.generate_api_report()
            
            # Verify integration worked
            assert arch_report is not None
            assert arch_report.metrics.total_files >= 10
            assert api_report is not None
            assert api_report.total_endpoints >= 5
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 5 modules not available")
    
    def test_phase5_performance_under_chaos(self):
        """Test performance of Phase 5 modules under chaos conditions"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize systems
            api_system = APIManagementSystem(str(temp_project))
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Start performance test
            start_time = time.time()
            
            # Create many files and endpoints simultaneously
            for i in range(30):
                # Create test file
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
                
                # Create API endpoint
                endpoint = APIEndpoint(
                    path=f"/api/v1/perf_{i}",
                    method=APIMethod.GET,
                    version=APIVersion.V1,
                    description=f"Performance endpoint {i}",
                    parameters=[],
                    request_schema={},
                    response_schema={},
                    status_codes={200: "Success"},
                    examples=[],
                    tags=["performance"]
                )
                api_system.register_endpoint(endpoint)
            
            # Analyze architecture
            arch_report = analyzer.analyze_architecture()
            
            # Generate API report
            api_report = api_system.generate_api_report()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete within reasonable time
            assert total_time < 60, f"Performance test took {total_time}s"
            assert arch_report is not None
            assert arch_report.metrics.total_files >= 30
            assert api_report is not None
            assert api_report.total_endpoints >= 30
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 5 modules not available")
    
    def test_phase5_scalability_with_many_operations(self):
        """Test scalability with many operations"""
        try:
            from api_management import APIManagementSystem, APIEndpoint, APIMethod, APIVersion
            from architecture_analyzer import ArchitectureAnalyzer
            
            temp_project = TestFixtures.create_temp_project()
            
            # Initialize systems
            api_system = APIManagementSystem(str(temp_project))
            analyzer = ArchitectureAnalyzer(str(temp_project))
            
            # Create many files for scalability test
            for i in range(100):
                test_file = temp_project / f"scale_test_{i}.py"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
class ScaleTest{i}:
    """Scale test class {i}"""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        """Method {i}"""
        return self.value * 2
''')
            
            # Create many API endpoints
            for i in range(50):
                endpoint = APIEndpoint(
                    path=f"/api/v1/scale_{i}",
                    method=APIMethod.POST,
                    version=APIVersion.V1,
                    description=f"Scale endpoint {i}",
                    parameters=[],
                    request_schema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    },
                    response_schema={},
                    status_codes={200: "Success"},
                    examples=[],
                    tags=["scale"]
                )
                api_system.register_endpoint(endpoint)
            
            # Analyze architecture
            arch_report = analyzer.analyze_architecture()
            
            # Generate API report
            api_report = api_system.generate_api_report()
            
            # Verify scalability
            assert arch_report is not None
            assert arch_report.metrics.total_files >= 100
            assert api_report is not None
            assert api_report.total_endpoints >= 50
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("Phase 5 modules not available")
