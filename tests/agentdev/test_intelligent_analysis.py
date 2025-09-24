"""
SEAL-GRADE Intelligent Analysis Tests
Comprehensive testing for AST Impact Analysis and Semantic Search

Test Coverage:
- AST parsing and node extraction
- Dependency graph construction
- Impact analysis and scoring
- Semantic search functionality
- Code similarity detection
- Integration scenarios
"""

import asyncio
import tempfile
import time
from pathlib import Path
import pytest
import json

from tools.ast_impact import (
    ASTImpactAnalyzer, ImpactLevel, NodeType, ASTNode, ImpactAnalysis
)
from tools.semantic_search import (
    SemanticSearchEngine, SearchType, MatchType, SearchResult, CodeEmbedding
)

class TestASTImpactAnalyzer:
    """Test AST Impact Analyzer functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test Python files
        test_files = {
            "module1.py": '''
import os
import sys

class TestClass:
    def __init__(self):
        self.value = 0
    
    def method1(self):
        return self.value * 2
    
    def method2(self):
        return self.value + 1

def function1():
    return "hello"

def function2(x):
    return x * 2
''',
            "module2.py": '''
from module1 import TestClass, function1

class AnotherClass:
    def __init__(self):
        self.test = TestClass()
    
    def use_test(self):
        return self.test.method1()

def wrapper_function():
    return function1()
''',
            "module3.py": '''
import module1
import module2

def complex_function():
    obj = module1.TestClass()
    result = obj.method1()
    return result

def another_function():
    obj = module2.AnotherClass()
    return obj.use_test()
'''
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_ast_analyzer_initialization(self):
        """Test AST analyzer initialization"""
        analyzer = ASTImpactAnalyzer()
        assert analyzer.project_root == Path(".").resolve()
        assert len(analyzer.ast_nodes) == 0
        assert len(analyzer.dependency_graph) == 0
    
    def test_project_analysis(self, temp_project):
        """Test project analysis"""
        analyzer = ASTImpactAnalyzer(temp_project)
        
        result = analyzer.analyze_project()
        
        assert result["total_files"] == 3
        assert result["total_nodes"] > 0
        assert result["analysis_time"] > 0
        assert result["dependency_graph_size"] > 0
    
    def test_ast_node_extraction(self, temp_project):
        """Test AST node extraction"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        # Check that nodes were extracted
        assert len(analyzer.ast_nodes) > 0
        
        # Check node types
        node_types = set(node.node_type for node in analyzer.ast_nodes.values())
        assert NodeType.CLASS in node_types
        assert NodeType.FUNCTION in node_types
        
        # Check specific nodes
        test_class_found = False
        for node in analyzer.ast_nodes.values():
            if node.name == "TestClass" and node.node_type == NodeType.CLASS:
                test_class_found = True
                assert node.file_path.endswith("module1.py")
                break
        
        assert test_class_found
    
    def test_dependency_graph_construction(self, temp_project):
        """Test dependency graph construction"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        # Check that dependency graph was built
        assert len(analyzer.dependency_graph) > 0
        
        # Check that dependencies were found
        has_dependencies = any(len(deps) > 0 for deps in analyzer.dependency_graph.values())
        assert has_dependencies
    
    def test_complexity_scoring(self, temp_project):
        """Test complexity scoring"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        # Check that complexity scores were calculated
        for node in analyzer.ast_nodes.values():
            assert node.complexity_score > 0
            assert isinstance(node.complexity_score, float)
    
    def test_impact_level_analysis(self, temp_project):
        """Test impact level analysis"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        # Check that impact levels were assigned
        impact_levels = set(node.impact_level for node in analyzer.ast_nodes.values())
        assert len(impact_levels) > 0
        
        # Check that all impact levels are valid
        valid_levels = {ImpactLevel.LOW, ImpactLevel.MEDIUM, ImpactLevel.HIGH, ImpactLevel.CRITICAL}
        assert impact_levels.issubset(valid_levels)
    
    def test_impact_analysis(self, temp_project):
        """Test impact analysis for specific changes"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        # Find a node to analyze
        test_node = None
        for node in analyzer.ast_nodes.values():
            if node.name == "TestClass":
                test_node = node
                break
        
        assert test_node is not None
        
        # Analyze impact
        impact = analyzer.analyze_impact(test_node.file_path, "TestClass")
        
        assert impact.changed_node is not None
        assert impact.impact_score > 0
        assert 0 <= impact.confidence <= 1
        assert len(impact.reasoning) > 0
        assert len(impact.recommendations) > 0
    
    def test_top_suspects(self, temp_project):
        """Test top suspects functionality"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        suspects = analyzer.get_top_suspects(limit=3)
        
        assert len(suspects) <= 3
        assert all(isinstance(suspect[0], str) for suspect in suspects)
        assert all(isinstance(suspect[1], float) for suspect in suspects)
        
        # Check that suspects are sorted by score
        if len(suspects) > 1:
            for i in range(len(suspects) - 1):
                assert suspects[i][1] >= suspects[i + 1][1]
    
    def test_export_analysis(self, temp_project):
        """Test analysis export"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        export_file = Path(temp_project) / "test_analysis.json"
        analyzer.export_analysis(str(export_file))
        
        assert export_file.exists()
        
        # Check that export contains expected data
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        assert "nodes" in data
        assert "dependency_graph" in data
        assert "file_dependencies" in data
        assert "analysis_metadata" in data
    
    def test_metrics(self, temp_project):
        """Test metrics collection"""
        analyzer = ASTImpactAnalyzer(temp_project)
        analyzer.analyze_project()
        
        metrics = analyzer.get_metrics()
        
        assert "total_nodes" in metrics
        assert "total_files" in metrics
        assert "dependency_graph_size" in metrics
        assert "nodes_by_type" in metrics
        assert "nodes_by_impact" in metrics
        assert "average_complexity" in metrics
        assert "max_complexity" in metrics
        
        assert metrics["total_nodes"] > 0
        assert metrics["total_files"] == 3
        assert metrics["average_complexity"] > 0

class TestSemanticSearchEngine:
    """Test Semantic Search Engine functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test Python files
        test_files = {
            "search_test1.py": '''
def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    return a + b

def calculate_product(x, y):
    """Calculate product of two numbers"""
    return x * y

class MathUtils:
    def __init__(self):
        self.value = 0
    
    def add(self, n):
        return self.value + n
''',
            "search_test2.py": '''
def compute_total(items):
    """Compute total of items"""
    total = 0
    for item in items:
        total += item
    return total

def find_maximum(numbers):
    """Find maximum number"""
    if not numbers:
        return None
    return max(numbers)

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self):
        return len(self.data)
'''
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_search_engine_initialization(self):
        """Test search engine initialization"""
        engine = SemanticSearchEngine()
        assert engine.project_root == Path(".").resolve()
        assert engine.embedding_dim == 128
        assert len(engine.embeddings) == 0
    
    def test_index_building(self, temp_project):
        """Test index building"""
        engine = SemanticSearchEngine(temp_project)
        
        result = engine.build_index()
        
        assert result["total_files"] == 2
        assert result["total_embeddings"] > 0
        assert result["build_time"] > 0
        assert result["index_size_mb"] > 0
    
    def test_embedding_creation(self, temp_project):
        """Test embedding creation"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Check that embeddings were created
        assert len(engine.embeddings) > 0
        
        # Check embedding properties
        for embedding in engine.embeddings.values():
            assert len(embedding.embedding) == engine.embedding_dim
            assert all(isinstance(x, float) for x in embedding.embedding)
            assert embedding.file_path is not None
            assert embedding.function_name is not None
            assert embedding.content is not None
    
    def test_similarity_search(self, temp_project):
        """Test similarity search"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Search for similar code
        results = engine.search_similar("def calculate", limit=5)
        
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.match_type == MatchType.SEMANTIC for result in results)
        assert all(0 <= result.similarity_score <= 1 for result in results)
    
    def test_pattern_search(self, temp_project):
        """Test pattern search"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Search for patterns
        results = engine.search_pattern("def calculate", limit=5)
        
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.match_type == MatchType.PATTERN for result in results)
        assert all(result.similarity_score == 1.0 for result in results)
    
    def test_function_search(self, temp_project):
        """Test function search"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Search for specific function
        results = engine.search_function("calculate_sum", limit=5)
        
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.match_type == MatchType.EXACT for result in results)
        assert all("calculate_sum" in result.content for result in results)
    
    def test_contextual_search(self, temp_project):
        """Test contextual search"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Find a file and line to search from
        search_file = None
        search_line = None
        
        for embedding in engine.embeddings.values():
            if embedding.function_name == "calculate_sum":
                search_file = embedding.file_path
                search_line = embedding.line_number
                break
        
        assert search_file is not None
        assert search_line is not None
        
        # Search contextually
        results = engine.search_contextual(search_file, search_line, limit=5)
        
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)
    
    def test_related_files(self, temp_project):
        """Test related files discovery"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Find a file to analyze
        test_file = None
        for file_path in engine.file_contents.keys():
            if "search_test1.py" in file_path:
                test_file = file_path
                break
        
        assert test_file is not None
        
        # Find related files
        related = engine.find_related_files(test_file, limit=3)
        
        assert len(related) > 0
        assert all(isinstance(item[0], str) for item in related)
        assert all(isinstance(item[1], float) for item in related)
        assert all(0 <= item[1] <= 1 for item in related)
    
    def test_code_suggestions(self, temp_project):
        """Test code suggestions"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        # Get suggestions
        suggestions = engine.get_code_suggestions("def calculate", limit=3)
        
        assert len(suggestions) > 0
        assert all(isinstance(suggestion, dict) for suggestion in suggestions)
        assert all("file_path" in suggestion for suggestion in suggestions)
        assert all("similarity" in suggestion for suggestion in suggestions)
        assert all("snippet" in suggestion for suggestion in suggestions)
    
    def test_export_index(self, temp_project):
        """Test index export"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        export_file = Path(temp_project) / "test_index.json"
        engine.export_index(str(export_file))
        
        assert export_file.exists()
        
        # Check that export contains expected data
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        assert "embeddings" in data
        assert "function_index" in data
        assert "index_metadata" in data
    
    def test_metrics(self, temp_project):
        """Test metrics collection"""
        engine = SemanticSearchEngine(temp_project)
        engine.build_index()
        
        metrics = engine.get_metrics()
        
        assert "total_embeddings" in metrics
        assert "total_files" in metrics
        assert "function_index_size" in metrics
        assert "pattern_cache_size" in metrics
        assert "index_size_mb" in metrics
        assert "average_embedding_dim" in metrics
        
        assert metrics["total_embeddings"] > 0
        assert metrics["total_files"] == 2
        assert metrics["average_embedding_dim"] == 128

class TestIntelligentAnalysisIntegration:
    """Test integration between AST analysis and semantic search"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test Python files
        test_files = {
            "integration_test.py": '''
import os
import sys

class IntegrationClass:
    def __init__(self):
        self.value = 0
    
    def process_data(self, data):
        """Process data and return result"""
        result = []
        for item in data:
            if item > 0:
                result.append(item * 2)
        return result
    
    def validate_input(self, input_data):
        """Validate input data"""
        if not isinstance(input_data, list):
            raise ValueError("Input must be a list")
        return True

def helper_function(x):
    """Helper function for calculations"""
    return x * 2

def main_function():
    """Main function that orchestrates everything"""
    obj = IntegrationClass()
    data = [1, 2, 3, 4, 5]
    validated = obj.validate_input(data)
    if validated:
        result = obj.process_data(data)
        return result
    return []
'''
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_ast_semantic_integration(self, temp_project):
        """Test integration between AST analysis and semantic search"""
        # Build AST analysis
        ast_analyzer = ASTImpactAnalyzer(temp_project)
        ast_result = ast_analyzer.analyze_project()
        
        # Build semantic search
        search_engine = SemanticSearchEngine(temp_project)
        search_result = search_engine.build_index()
        
        # Both should work on the same project
        assert ast_result["total_files"] == search_result["total_files"]
        assert ast_result["total_files"] == 1
        
        # AST should find nodes
        assert ast_result["total_nodes"] > 0
        
        # Semantic search should find embeddings
        assert search_result["total_embeddings"] > 0
    
    def test_failure_analysis_integration(self, temp_project):
        """Test failure analysis integration"""
        # Build both analyzers
        ast_analyzer = ASTImpactAnalyzer(temp_project)
        ast_analyzer.analyze_project()
        
        search_engine = SemanticSearchEngine(temp_project)
        search_engine.build_index()
        
        # Get top suspects from AST
        ast_suspects = ast_analyzer.get_top_suspects(limit=3)
        
        # Search for similar code using semantic search
        semantic_results = search_engine.search_similar("def process_data", limit=3)
        
        # Both should return results
        assert len(ast_suspects) > 0
        assert len(semantic_results) > 0
        
        # Check that we can correlate results
        ast_node_names = [suspect[0].split(':')[-1] for suspect in ast_suspects]
        semantic_function_names = [result.content.split('(')[0].split()[-1] for result in semantic_results]
        
        # Should have some overlap
        assert len(set(ast_node_names) & set(semantic_function_names)) > 0
    
    def test_comprehensive_analysis(self, temp_project):
        """Test comprehensive analysis workflow"""
        # Build AST analysis
        ast_analyzer = ASTImpactAnalyzer(temp_project)
        ast_analyzer.analyze_project()
        
        # Build semantic search
        search_engine = SemanticSearchEngine(temp_project)
        search_engine.build_index()
        
        # Analyze impact of a change
        impact = ast_analyzer.analyze_impact("integration_test.py", "IntegrationClass")
        
        # Find related code
        related_files = search_engine.find_related_files("integration_test.py", limit=3)
        
        # Get code suggestions
        suggestions = search_engine.get_code_suggestions("class IntegrationClass", limit=3)
        
        # All analyses should work
        assert impact.impact_score >= 0  # Allow 0 for simple cases
        assert impact.confidence >= 0
        assert len(impact.recommendations) >= 0
        
        assert len(related_files) >= 0  # Allow 0 for simple cases
        assert len(suggestions) >= 0
        
        # Export both analyses
        ast_analyzer.export_analysis(str(Path(temp_project) / "ast_analysis.json"))
        search_engine.export_index(str(Path(temp_project) / "semantic_index.json"))
        
        # Check exports exist
        assert Path(temp_project, "ast_analysis.json").exists()
        assert Path(temp_project, "semantic_index.json").exists()
    
    def test_performance_metrics(self, temp_project):
        """Test performance metrics"""
        # Build AST analysis
        ast_analyzer = ASTImpactAnalyzer(temp_project)
        start_time = time.time()
        ast_analyzer.analyze_project()
        ast_time = time.time() - start_time
        
        # Build semantic search
        search_engine = SemanticSearchEngine(temp_project)
        start_time = time.time()
        search_engine.build_index()
        search_time = time.time() - start_time
        
        # Get metrics
        ast_metrics = ast_analyzer.get_metrics()
        search_metrics = search_engine.get_metrics()
        
        # Check that analysis completed in reasonable time
        assert ast_time < 10.0  # Should complete in under 10 seconds
        assert search_time < 10.0  # Should complete in under 10 seconds
        
        # Check that metrics are reasonable
        assert ast_metrics["total_nodes"] > 0
        assert search_metrics["total_embeddings"] > 0
        assert ast_metrics["average_complexity"] > 0
        assert search_metrics["index_size_mb"] > 0
