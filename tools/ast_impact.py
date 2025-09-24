"""
AST Impact Analysis for AgentDev
SEAL-GRADE Intelligent Code Analysis

Features:
- Parse Python AST to map functions/classes to affected files
- Dependency graph analysis
- Impact assessment for code changes
- Confidence scoring for failure analysis
- Integration with test failure analysis
"""

import ast
import os
import re
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class ImpactLevel(Enum):
    """Impact level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NodeType(Enum):
    """AST node type enumeration"""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    MODULE = "module"

@dataclass
class ASTNode:
    """AST node information"""
    name: str
    node_type: NodeType
    file_path: str
    line_number: int
    end_line: int
    dependencies: Set[str]
    dependents: Set[str]
    complexity_score: float
    impact_level: ImpactLevel
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ImpactAnalysis:
    """Impact analysis result"""
    changed_node: str
    affected_files: List[str]
    affected_functions: List[str]
    affected_classes: List[str]
    impact_score: float
    confidence: float
    reasoning: str
    recommendations: List[str]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ASTImpactAnalyzer:
    """SEAL-GRADE AST Impact Analyzer"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.ast_nodes: Dict[str, ASTNode] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.file_dependencies: Dict[str, Set[str]] = {}
        self._complexity_cache: Dict[str, float] = {}
        
    def analyze_project(self, include_patterns: List[str] = None, 
                       exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """Analyze entire project for AST impact"""
        if include_patterns is None:
            include_patterns = ["*.py"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.pyc", ".git", "node_modules", "tests"]
        
        start_time = time.time()
        
        # Find all Python files
        python_files = self._find_python_files(include_patterns, exclude_patterns)
        
        # Parse AST for each file
        for file_path in python_files:
            try:
                self._parse_file_ast(file_path)
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Calculate complexity scores
        self._calculate_complexity_scores()
        
        # Analyze impact levels
        self._analyze_impact_levels()
        
        analysis_time = time.time() - start_time
        
        return {
            "total_files": len(python_files),
            "total_nodes": len(self.ast_nodes),
            "analysis_time": analysis_time,
            "dependency_graph_size": len(self.dependency_graph),
            "high_impact_nodes": len([n for n in self.ast_nodes.values() if n.impact_level == ImpactLevel.HIGH]),
            "critical_nodes": len([n for n in self.ast_nodes.values() if n.impact_level == ImpactLevel.CRITICAL])
        }
    
    def _find_python_files(self, include_patterns: List[str], exclude_patterns: List[str]) -> List[Path]:
        """Find Python files matching patterns"""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(self._match_pattern(pattern, d) for pattern in exclude_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    # Check if file should be included
                    if any(self._match_pattern(pattern, str(file_path.relative_to(self.project_root))) for pattern in include_patterns):
                        python_files.append(file_path)
        
        return python_files
    
    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Match pattern with proper escaping"""
        try:
            # Skip empty patterns
            if not pattern:
                return False
            # Convert glob pattern to regex
            if '*' in pattern:
                # Escape special regex characters except *
                escaped = re.escape(pattern).replace(r'\*', '.*')
                return bool(re.match(escaped, text))
            else:
                return pattern == text
        except re.error:
            # Fallback to simple string matching
            return pattern == text
    
    def _parse_file_ast(self, file_path: Path):
        """Parse AST for a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # Extract imports
            imports = self._extract_imports(tree)
            
            # Extract functions and classes
            functions = self._extract_functions(tree, file_path)
            classes = self._extract_classes(tree, file_path)
            
            # Store nodes
            for func in functions:
                node_id = f"{file_path}:{func['name']}"
                self.ast_nodes[node_id] = ASTNode(
                    name=func['name'],
                    node_type=NodeType.FUNCTION,
                    file_path=str(file_path),
                    line_number=func['line'],
                    end_line=func['end_line'],
                    dependencies=set(imports),
                    dependents=set(),
                    complexity_score=0.0,
                    impact_level=ImpactLevel.LOW,
                    metadata={"args": func.get('args', []), "decorators": func.get('decorators', [])}
                )
            
            for cls in classes:
                node_id = f"{file_path}:{cls['name']}"
                self.ast_nodes[node_id] = ASTNode(
                    name=cls['name'],
                    node_type=NodeType.CLASS,
                    file_path=str(file_path),
                    line_number=cls['line'],
                    end_line=cls['end_line'],
                    dependencies=set(imports),
                    dependents=set(),
                    complexity_score=0.0,
                    impact_level=ImpactLevel.LOW,
                    metadata={"bases": cls.get('bases', []), "methods": cls.get('methods', [])}
                )
            
            # Store file dependencies
            self.file_dependencies[str(file_path)] = set(imports)
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    
    def _extract_functions(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """Extract function definitions from AST"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': node.end_lineno or node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list]
                })
        
        return functions
    
    def _extract_classes(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """Extract class definitions from AST"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': node.end_lineno or node.lineno,
                    'bases': [self._get_base_name(base) for base in node.bases],
                    'methods': methods
                })
        
        return classes
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        else:
            return str(decorator)
    
    def _get_base_name(self, base: ast.AST) -> str:
        """Get base class name from AST node"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}"
        else:
            return str(base)
    
    def _build_dependency_graph(self):
        """Build dependency graph between nodes"""
        for node_id, node in self.ast_nodes.items():
            self.dependency_graph[node_id] = set()
            
            # Find dependencies based on imports and usage
            for dep_node_id, dep_node in self.ast_nodes.items():
                if dep_node.file_path != node.file_path:
                    # Check if node uses something from dep_node
                    if self._has_dependency(node, dep_node):
                        self.dependency_graph[node_id].add(dep_node_id)
                        dep_node.dependents.add(node_id)
    
    def _has_dependency(self, node: ASTNode, dep_node: ASTNode) -> bool:
        """Check if node has dependency on dep_node"""
        # Simple heuristic: check if node's file imports dep_node's module
        node_file = Path(node.file_path)
        dep_file = Path(dep_node.file_path)
        
        # Check if node's file imports the module containing dep_node
        if dep_file.stem in str(node.dependencies):
            return True
        
        # Check for relative imports
        try:
            relative_path = dep_file.relative_to(node_file.parent)
            if str(relative_path).replace('\\', '.').replace('/', '.') in str(node.dependencies):
                return True
        except ValueError:
            pass
        
        return False
    
    def _calculate_complexity_scores(self):
        """Calculate complexity scores for nodes"""
        for node_id, node in self.ast_nodes.items():
            complexity = 1.0  # Base complexity
            
            # Add complexity based on dependencies
            complexity += len(node.dependencies) * 0.1
            
            # Add complexity based on dependents
            complexity += len(node.dependents) * 0.2
            
            # Add complexity based on node type
            if node.node_type == NodeType.CLASS:
                complexity += 0.5
            elif node.node_type == NodeType.METHOD:
                complexity += 0.3
            
            # Add complexity based on metadata
            if node.metadata:
                if 'args' in node.metadata:
                    complexity += len(node.metadata['args']) * 0.1
                if 'methods' in node.metadata:
                    complexity += len(node.metadata['methods']) * 0.2
            
            node.complexity_score = complexity
            self._complexity_cache[node_id] = complexity
    
    def _analyze_impact_levels(self):
        """Analyze impact levels for nodes"""
        for node_id, node in self.ast_nodes.items():
            impact_score = node.complexity_score
            
            # Adjust impact based on dependents
            impact_score += len(node.dependents) * 0.5
            
            # Adjust impact based on node type
            if node.node_type == NodeType.CLASS:
                impact_score += 1.0
            elif node.node_type == NodeType.FUNCTION:
                impact_score += 0.5
            
            # Determine impact level
            if impact_score >= 5.0:
                node.impact_level = ImpactLevel.CRITICAL
            elif impact_score >= 3.0:
                node.impact_level = ImpactLevel.HIGH
            elif impact_score >= 2.0:
                node.impact_level = ImpactLevel.MEDIUM
            else:
                node.impact_level = ImpactLevel.LOW
    
    def analyze_impact(self, changed_file: str, changed_function: str = None) -> ImpactAnalysis:
        """Analyze impact of changes to a specific function/class"""
        # Find the changed node
        changed_node_id = None
        for node_id, node in self.ast_nodes.items():
            if changed_file in node.file_path:
                if changed_function is None or node.name == changed_function:
                    changed_node_id = node_id
                    break
        
        if not changed_node_id:
            return ImpactAnalysis(
                changed_node=f"{changed_file}:{changed_function}",
                affected_files=[],
                affected_functions=[],
                affected_classes=[],
                impact_score=0.0,
                confidence=0.0,
                reasoning="Node not found in AST analysis",
                recommendations=["Ensure file is included in analysis"]
            )
        
        changed_node = self.ast_nodes[changed_node_id]
        
        # Find affected nodes
        affected_nodes = self._find_affected_nodes(changed_node_id)
        
        # Calculate impact score
        impact_score = self._calculate_impact_score(changed_node, affected_nodes)
        
        # Calculate confidence
        confidence = self._calculate_confidence(changed_node, affected_nodes)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(changed_node, affected_nodes)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(changed_node, affected_nodes)
        
        return ImpactAnalysis(
            changed_node=changed_node_id,
            affected_files=list(set(node.file_path for node in affected_nodes)),
            affected_functions=[node.name for node in affected_nodes if node.node_type == NodeType.FUNCTION],
            affected_classes=[node.name for node in affected_nodes if node.node_type == NodeType.CLASS],
            impact_score=impact_score,
            confidence=confidence,
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def _find_affected_nodes(self, changed_node_id: str) -> List[ASTNode]:
        """Find nodes affected by changes to changed_node"""
        affected = set()
        to_process = [changed_node_id]
        
        while to_process:
            current_id = to_process.pop(0)
            if current_id in affected:
                continue
            
            affected.add(current_id)
            current_node = self.ast_nodes[current_id]
            
            # Add all dependents
            for dependent_id in current_node.dependents:
                if dependent_id not in affected:
                    to_process.append(dependent_id)
        
        return [self.ast_nodes[node_id] for node_id in affected if node_id in self.ast_nodes]
    
    def _calculate_impact_score(self, changed_node: ASTNode, affected_nodes: List[ASTNode]) -> float:
        """Calculate impact score for changes"""
        base_score = changed_node.complexity_score
        
        # Add scores from affected nodes
        affected_score = sum(node.complexity_score for node in affected_nodes)
        
        # Weight by impact level
        level_weights = {
            ImpactLevel.LOW: 1.0,
            ImpactLevel.MEDIUM: 2.0,
            ImpactLevel.HIGH: 3.0,
            ImpactLevel.CRITICAL: 5.0
        }
        
        weighted_score = sum(
            node.complexity_score * level_weights[node.impact_level]
            for node in affected_nodes
        )
        
        return base_score + affected_score + weighted_score * 0.1
    
    def _calculate_confidence(self, changed_node: ASTNode, affected_nodes: List[ASTNode]) -> float:
        """Calculate confidence in impact analysis"""
        # Base confidence
        confidence = 0.7
        
        # Increase confidence based on number of dependencies
        if len(changed_node.dependencies) > 0:
            confidence += 0.1
        
        # Increase confidence based on number of dependents
        if len(changed_node.dependents) > 0:
            confidence += 0.1
        
        # Decrease confidence if too many affected nodes (might be over-estimation)
        if len(affected_nodes) > 20:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_reasoning(self, changed_node: ASTNode, affected_nodes: List[ASTNode]) -> str:
        """Generate reasoning for impact analysis"""
        reasoning_parts = []
        
        reasoning_parts.append(f"Changed {changed_node.node_type.value} '{changed_node.name}' in {Path(changed_node.file_path).name}")
        
        if changed_node.dependencies:
            reasoning_parts.append(f"Has {len(changed_node.dependencies)} dependencies")
        
        if changed_node.dependents:
            reasoning_parts.append(f"Has {len(changed_node.dependents)} dependents")
        
        if affected_nodes:
            reasoning_parts.append(f"Affects {len(affected_nodes)} total nodes")
        
        # Add specific impact details
        high_impact = [n for n in affected_nodes if n.impact_level == ImpactLevel.HIGH]
        if high_impact:
            reasoning_parts.append(f"High impact on {len(high_impact)} nodes")
        
        critical_impact = [n for n in affected_nodes if n.impact_level == ImpactLevel.CRITICAL]
        if critical_impact:
            reasoning_parts.append(f"Critical impact on {len(critical_impact)} nodes")
        
        return ". ".join(reasoning_parts) + "."
    
    def _generate_recommendations(self, changed_node: ASTNode, affected_nodes: List[ASTNode]) -> List[str]:
        """Generate recommendations for impact analysis"""
        recommendations = []
        
        if changed_node.impact_level == ImpactLevel.CRITICAL:
            recommendations.append("Consider breaking down this change into smaller parts")
            recommendations.append("Run comprehensive tests before deployment")
        
        if len(affected_nodes) > 10:
            recommendations.append("Review affected files carefully")
            recommendations.append("Consider running integration tests")
        
        high_impact_nodes = [n for n in affected_nodes if n.impact_level == ImpactLevel.HIGH]
        if high_impact_nodes:
            recommendations.append("Pay special attention to high-impact affected nodes")
        
        if changed_node.node_type == NodeType.CLASS:
            recommendations.append("Check if class interface changes affect subclasses")
        
        if changed_node.node_type == NodeType.FUNCTION:
            recommendations.append("Verify function signature changes don't break callers")
        
        return recommendations
    
    def get_top_suspects(self, test_failure_context: str = None, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top suspects for test failures"""
        suspects = []
        
        for node_id, node in self.ast_nodes.items():
            # Calculate suspect score based on various factors
            suspect_score = node.complexity_score
            
            # Boost score for high-impact nodes
            if node.impact_level == ImpactLevel.HIGH:
                suspect_score *= 1.5
            elif node.impact_level == ImpactLevel.CRITICAL:
                suspect_score *= 2.0
            
            # Boost score for nodes with many dependents
            suspect_score += len(node.dependents) * 0.3
            
            # Boost score if test failure context matches
            if test_failure_context:
                if test_failure_context.lower() in node.name.lower():
                    suspect_score *= 1.2
                if test_failure_context.lower() in node.file_path.lower():
                    suspect_score *= 1.1
            
            suspects.append((node_id, suspect_score))
        
        # Sort by suspect score and return top N
        suspects.sort(key=lambda x: x[1], reverse=True)
        return suspects[:limit]
    
    def export_analysis(self, output_file: str = "ast_analysis.json"):
        """Export analysis results to JSON"""
        import json
        
        analysis_data = {
            "nodes": {node_id: asdict(node) for node_id, node in self.ast_nodes.items()},
            "dependency_graph": {node_id: list(deps) for node_id, deps in self.dependency_graph.items()},
            "file_dependencies": {file_path: list(deps) for file_path, deps in self.file_dependencies.items()},
            "complexity_cache": self._complexity_cache,
            "analysis_metadata": {
                "project_root": str(self.project_root),
                "total_nodes": len(self.ast_nodes),
                "analysis_timestamp": time.time()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        logger.info(f"AST analysis exported to {output_file}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get analysis metrics"""
        return {
            "total_nodes": len(self.ast_nodes),
            "total_files": len(self.file_dependencies),
            "dependency_graph_size": len(self.dependency_graph),
            "nodes_by_type": {
                node_type.value: len([n for n in self.ast_nodes.values() if n.node_type == node_type])
                for node_type in NodeType
            },
            "nodes_by_impact": {
                impact_level.value: len([n for n in self.ast_nodes.values() if n.impact_level == impact_level])
                for impact_level in ImpactLevel
            },
            "average_complexity": sum(n.complexity_score for n in self.ast_nodes.values()) / len(self.ast_nodes) if self.ast_nodes else 0,
            "max_complexity": max((n.complexity_score for n in self.ast_nodes.values()), default=0)
        }
