#!/usr/bin/env python3
"""
AgentDev AST Analyzer - Intelligent code analysis
Impact assessment, semantic understanding, and intelligent code analysis
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib

@dataclass
class CodeElement:
    """Code element analysis"""
    name: str
    type: str
    line_number: int
    complexity: int
    dependencies: List[str]
    impact_score: float
    semantic_tags: List[str]

@dataclass
class ImpactAnalysis:
    """Impact analysis result"""
    file_path: str
    change_type: str
    affected_elements: List[CodeElement]
    impact_score: float
    risk_level: str
    suggestions: List[str]

@dataclass
class SemanticContext:
    """Semantic context"""
    context_type: str
    keywords: List[str]
    relationships: List[str]
    confidence: float

class ASTAnalyzer:
    """Intelligent AST-based code analyzer"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.code_elements = {}
        self.dependency_graph = defaultdict(set)
        self.semantic_contexts = {}
        self.impact_cache = {}
    
    async def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze entire codebase"""
        print("🔍 Analyzing codebase with AST...")
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        analysis_results = {
            "files_analyzed": 0,
            "total_elements": 0,
            "complexity_score": 0,
            "dependency_count": 0,
            "semantic_contexts": 0
        }
        
        for file_path in python_files:
            try:
                await self._analyze_file(file_path)
                analysis_results["files_analyzed"] += 1
            except Exception as e:
                print(f"⚠️ Could not analyze {file_path}: {e}")
        
        # Calculate metrics
        analysis_results["total_elements"] = len(self.code_elements)
        analysis_results["complexity_score"] = self._calculate_complexity_score()
        analysis_results["dependency_count"] = len(self.dependency_graph)
        analysis_results["semantic_contexts"] = len(self.semantic_contexts)
        
        print(f"✅ Codebase analysis completed: {analysis_results}")
        
        return analysis_results
    
    async def _analyze_file(self, file_path: Path):
        """Analyze individual file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Analyze AST nodes
            await self._analyze_ast_nodes(file_path, tree)
            
            # Extract semantic context
            await self._extract_semantic_context(file_path, content)
            
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
    
    async def _analyze_ast_nodes(self, file_path: Path, tree: ast.AST):
        """Analyze AST nodes"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                await self._analyze_function(file_path, node)
            elif isinstance(node, ast.ClassDef):
                await self._analyze_class(file_path, node)
            elif isinstance(node, ast.Import):
                await self._analyze_import(file_path, node)
            elif isinstance(node, ast.ImportFrom):
                await self._analyze_import_from(file_path, node)
    
    async def _analyze_function(self, file_path: Path, node: ast.FunctionDef):
        """Analyze function definition"""
        element_id = f"{file_path}:{node.name}"
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(node)
        
        # Calculate impact score
        impact_score = self._calculate_impact_score(node, complexity, dependencies)
        
        # Extract semantic tags
        semantic_tags = self._extract_semantic_tags(node)
        
        element = CodeElement(
            name=node.name,
            type="function",
            line_number=node.lineno,
            complexity=complexity,
            dependencies=dependencies,
            impact_score=impact_score,
            semantic_tags=semantic_tags
        )
        
        self.code_elements[element_id] = element
        
        # Update dependency graph
        for dep in dependencies:
            self.dependency_graph[element_id].add(dep)
    
    async def _analyze_class(self, file_path: Path, node: ast.ClassDef):
        """Analyze class definition"""
        element_id = f"{file_path}:{node.name}"
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(node)
        
        # Calculate impact score
        impact_score = self._calculate_impact_score(node, complexity, dependencies)
        
        # Extract semantic tags
        semantic_tags = self._extract_semantic_tags(node)
        
        element = CodeElement(
            name=node.name,
            type="class",
            line_number=node.lineno,
            complexity=complexity,
            dependencies=dependencies,
            impact_score=impact_score,
            semantic_tags=semantic_tags
        )
        
        self.code_elements[element_id] = element
        
        # Update dependency graph
        for dep in dependencies:
            self.dependency_graph[element_id].add(dep)
    
    async def _analyze_import(self, file_path: Path, node: ast.Import):
        """Analyze import statement"""
        for alias in node.names:
            element_id = f"{file_path}:import:{alias.name}"
            
            element = CodeElement(
                name=alias.name,
                type="import",
                line_number=node.lineno,
                complexity=1,
                dependencies=[],
                impact_score=0.5,
                semantic_tags=["external_dependency"]
            )
            
            self.code_elements[element_id] = element
    
    async def _analyze_import_from(self, file_path: Path, node: ast.ImportFrom):
        """Analyze import from statement"""
        if node.module:
            element_id = f"{file_path}:import_from:{node.module}"
            
            element = CodeElement(
                name=node.module,
                type="import_from",
                line_number=node.lineno,
                complexity=1,
                dependencies=[],
                impact_score=0.5,
                semantic_tags=["external_dependency"]
            )
            
            self.code_elements[element_id] = element
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """Extract dependencies from AST node"""
        dependencies = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.append(child.id)
            elif isinstance(child, ast.Attribute):
                dependencies.append(child.attr)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies.append(child.func.attr)
        
        return list(set(dependencies))
    
    def _calculate_impact_score(self, node: ast.AST, complexity: int, dependencies: List[str]) -> float:
        """Calculate impact score for code element"""
        base_score = 0.5
        
        # Complexity factor
        complexity_factor = min(complexity / 10, 1.0)
        
        # Dependencies factor
        dependency_factor = min(len(dependencies) / 20, 1.0)
        
        # Type factor
        type_factor = 1.0
        if isinstance(node, ast.ClassDef):
            type_factor = 1.5
        elif isinstance(node, ast.FunctionDef):
            type_factor = 1.2
        
        impact_score = base_score + (complexity_factor * 0.3) + (dependency_factor * 0.2) + (type_factor * 0.1)
        
        return min(impact_score, 1.0)
    
    def _extract_semantic_tags(self, node: ast.AST) -> List[str]:
        """Extract semantic tags from AST node"""
        tags = []
        
        # Analyze docstring
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node):
            docstring = ast.get_docstring(node).lower()
            
            if "async" in docstring:
                tags.append("async")
            if "test" in docstring:
                tags.append("test")
            if "api" in docstring:
                tags.append("api")
            if "database" in docstring or "db" in docstring:
                tags.append("database")
            if "security" in docstring:
                tags.append("security")
            if "performance" in docstring:
                tags.append("performance")
        
        # Analyze function/class name
        name = node.name.lower()
        
        if "test" in name:
            tags.append("test")
        if "api" in name:
            tags.append("api")
        if "db" in name or "database" in name:
            tags.append("database")
        if "auth" in name or "security" in name:
            tags.append("security")
        if "cache" in name:
            tags.append("cache")
        if "async" in name:
            tags.append("async")
        
        return list(set(tags))
    
    async def _extract_semantic_context(self, file_path: Path, content: str):
        """Extract semantic context from file content"""
        context_id = str(file_path)
        
        # Extract keywords
        keywords = self._extract_keywords(content)
        
        # Extract relationships
        relationships = self._extract_relationships(content)
        
        # Calculate confidence
        confidence = self._calculate_context_confidence(keywords, relationships)
        
        context = SemanticContext(
            context_type="file",
            keywords=keywords,
            relationships=relationships,
            confidence=confidence
        )
        
        self.semantic_contexts[context_id] = context
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Common programming keywords
        keywords = []
        
        # Technical terms
        tech_terms = [
            "async", "await", "database", "api", "test", "security",
            "performance", "cache", "authentication", "authorization",
            "encryption", "validation", "error", "exception", "logging"
        ]
        
        content_lower = content.lower()
        for term in tech_terms:
            if term in content_lower:
                keywords.append(term)
        
        return keywords
    
    def _extract_relationships(self, content: str) -> List[str]:
        """Extract relationships from content"""
        relationships = []
        
        # Import relationships
        import_pattern = r'from\s+(\w+)\s+import'
        imports = re.findall(import_pattern, content)
        relationships.extend([f"imports_from_{imp}" for imp in imports])
        
        # Class inheritance
        class_pattern = r'class\s+\w+\((\w+)\)'
        inheritances = re.findall(class_pattern, content)
        relationships.extend([f"inherits_from_{inh}" for inh in inheritances])
        
        return relationships
    
    def _calculate_context_confidence(self, keywords: List[str], relationships: List[str]) -> float:
        """Calculate confidence in semantic context"""
        if not keywords and not relationships:
            return 0.0
        
        keyword_score = min(len(keywords) / 10, 1.0)
        relationship_score = min(len(relationships) / 5, 1.0)
        
        return (keyword_score + relationship_score) / 2
    
    def _calculate_complexity_score(self) -> float:
        """Calculate overall complexity score"""
        if not self.code_elements:
            return 0.0
        
        total_complexity = sum(element.complexity for element in self.code_elements.values())
        avg_complexity = total_complexity / len(self.code_elements)
        
        return min(avg_complexity / 10, 1.0)
    
    async def analyze_impact(self, file_path: str, change_type: str) -> ImpactAnalysis:
        """Analyze impact of changes to a file"""
        print(f"🔍 Analyzing impact for {file_path}")
        
        # Find affected elements
        affected_elements = []
        for element_id, element in self.code_elements.items():
            if file_path in element_id:
                affected_elements.append(element)
        
        # Calculate impact score
        impact_score = self._calculate_impact_score_for_change(affected_elements, change_type)
        
        # Determine risk level
        risk_level = self._determine_risk_level(impact_score)
        
        # Generate suggestions
        suggestions = self._generate_impact_suggestions(affected_elements, change_type)
        
        analysis = ImpactAnalysis(
            file_path=file_path,
            change_type=change_type,
            affected_elements=affected_elements,
            impact_score=impact_score,
            risk_level=risk_level,
            suggestions=suggestions
        )
        
        return analysis
    
    def _calculate_impact_score_for_change(self, elements: List[CodeElement], change_type: str) -> float:
        """Calculate impact score for a change"""
        if not elements:
            return 0.0
        
        # Base impact from elements
        base_impact = sum(element.impact_score for element in elements) / len(elements)
        
        # Change type multiplier
        change_multipliers = {
            "add": 0.5,
            "modify": 1.0,
            "delete": 1.5,
            "refactor": 0.8
        }
        
        multiplier = change_multipliers.get(change_type, 1.0)
        
        return min(base_impact * multiplier, 1.0)
    
    def _determine_risk_level(self, impact_score: float) -> str:
        """Determine risk level based on impact score"""
        if impact_score < 0.3:
            return "low"
        elif impact_score < 0.6:
            return "medium"
        else:
            return "high"
    
    def _generate_impact_suggestions(self, elements: List[CodeElement], change_type: str) -> List[str]:
        """Generate suggestions based on impact analysis"""
        suggestions = []
        
        if not elements:
            return suggestions
        
        # High complexity elements
        high_complexity = [e for e in elements if e.complexity > 5]
        if high_complexity:
            suggestions.append("Consider refactoring high-complexity elements")
        
        # High impact elements
        high_impact = [e for e in elements if e.impact_score > 0.8]
        if high_impact:
            suggestions.append("Review high-impact elements for potential issues")
        
        # Security-related elements
        security_elements = [e for e in elements if "security" in e.semantic_tags]
        if security_elements:
            suggestions.append("Review security implications of changes")
        
        # Database-related elements
        db_elements = [e for e in elements if "database" in e.semantic_tags]
        if db_elements:
            suggestions.append("Consider database migration implications")
        
        return suggestions
    
    async def find_related_code(self, query: str, limit: int = 10) -> List[CodeElement]:
        """Find code elements related to a query"""
        query_lower = query.lower()
        related_elements = []
        
        for element_id, element in self.code_elements.items():
            score = 0
            
            # Name matching
            if query_lower in element.name.lower():
                score += 2
            
            # Semantic tag matching
            for tag in element.semantic_tags:
                if query_lower in tag.lower():
                    score += 1
            
            # Dependency matching
            for dep in element.dependencies:
                if query_lower in dep.lower():
                    score += 0.5
            
            if score > 0:
                related_elements.append((element, score))
        
        # Sort by score and return top results
        related_elements.sort(key=lambda x: x[1], reverse=True)
        return [element for element, score in related_elements[:limit]]
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary"""
        return {
            "total_elements": len(self.code_elements),
            "complexity_score": self._calculate_complexity_score(),
            "dependency_count": len(self.dependency_graph),
            "semantic_contexts": len(self.semantic_contexts),
            "element_types": Counter(element.type for element in self.code_elements.values()),
            "semantic_tags": Counter(tag for element in self.code_elements.values() for tag in element.semantic_tags)
        }
    
    async def export_analysis_report(self, output_path: str):
        """Export analysis report"""
        report_data = {
            "summary": self.get_analysis_summary(),
            "elements": {k: asdict(v) for k, v in self.code_elements.items()},
            "semantic_contexts": {k: asdict(v) for k, v in self.semantic_contexts.items()},
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Analysis report exported to {output_path}")

# Example usage
async def main():
    """Example usage of ASTAnalyzer"""
    analyzer = ASTAnalyzer(".")
    
    # Analyze codebase
    analysis_results = await analyzer.analyze_codebase()
    print(f"Analysis Results: {analysis_results}")
    
    # Analyze impact of changes
    impact_analysis = await analyzer.analyze_impact("agentdev/state_store.py", "modify")
    print(f"Impact Analysis: {impact_analysis}")
    
    # Find related code
    related_code = await analyzer.find_related_code("database", limit=5)
    print(f"Related Code: {len(related_code)} elements found")
    
    # Export report
    await analyzer.export_analysis_report("reports/ast_analysis_report.json")
    
    # Get summary
    summary = analyzer.get_analysis_summary()
    print(f"Analysis Summary: {summary}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
