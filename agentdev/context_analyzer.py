#!/usr/bin/env python3
"""
AgentDev Context Analyzer - Deep project context analysis
Analyzes project structure, coding conventions, dependency graph, and business goals
"""

import ast
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import networkx as nx

@dataclass
class ProjectContext:
    """Project context information"""
    project_name: str
    language: str
    framework: str
    architecture_pattern: str
    coding_conventions: Dict[str, Any]
    dependency_graph: Dict[str, List[str]]
    business_goals: List[str]
    technical_constraints: List[str]
    team_preferences: Dict[str, Any]

@dataclass
class CodePattern:
    """Code pattern analysis"""
    pattern_type: str
    frequency: int
    examples: List[str]
    confidence: float

@dataclass
class DependencyNode:
    """Dependency node information"""
    name: str
    type: str
    imports: List[str]
    exports: List[str]
    complexity: int
    dependencies: List[str]

class ContextAnalyzer:
    """Deep project context analyzer"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.context = ProjectContext(
            project_name="",
            language="python",
            framework="",
            architecture_pattern="",
            coding_conventions={},
            dependency_graph={},
            business_goals=[],
            technical_constraints=[],
            team_preferences={}
        )
        self.dependency_graph = nx.DiGraph()
        self.code_patterns = []
        self.dependency_nodes = {}
    
    async def analyze_project(self) -> ProjectContext:
        """Analyze entire project context"""
        print("🔍 Analyzing project context...")
        
        # Analyze project structure
        await self._analyze_project_structure()
        
        # Analyze coding conventions
        await self._analyze_coding_conventions()
        
        # Analyze dependency graph
        await self._analyze_dependency_graph()
        
        # Analyze business goals
        await self._analyze_business_goals()
        
        # Analyze technical constraints
        await self._analyze_technical_constraints()
        
        # Analyze team preferences
        await self._analyze_team_preferences()
        
        print("✅ Project context analysis completed")
        return self.context
    
    async def _analyze_project_structure(self):
        """Analyze project structure"""
        print("📁 Analyzing project structure...")
        
        # Detect project type
        if (self.project_root / "pyproject.toml").exists():
            self.context.framework = "modern_python"
        elif (self.project_root / "setup.py").exists():
            self.context.framework = "traditional_python"
        elif (self.project_root / "package.json").exists():
            self.context.language = "javascript"
            self.context.framework = "nodejs"
        
        # Analyze architecture pattern
        if (self.project_root / "agentdev").exists():
            self.context.architecture_pattern = "microservices"
        elif (self.project_root / "src").exists():
            self.context.architecture_pattern = "layered"
        else:
            self.context.architecture_pattern = "monolithic"
        
        # Set project name
        self.context.project_name = self.project_root.name
    
    async def _analyze_coding_conventions(self):
        """Analyze coding conventions"""
        print("📝 Analyzing coding conventions...")
        
        conventions = {
            "naming_style": "snake_case",
            "docstring_style": "google",
            "type_hints": True,
            "async_usage": True,
            "error_handling": "exception_based",
            "logging": "structured"
        }
        
        # Analyze Python files for conventions
        python_files = list(self.project_root.rglob("*.py"))
        if python_files:
            await self._analyze_python_conventions(python_files, conventions)
        
        self.context.coding_conventions = conventions
    
    async def _analyze_python_conventions(self, files: List[Path], conventions: Dict[str, Any]):
        """Analyze Python-specific conventions"""
        snake_case_count = 0
        camel_case_count = 0
        type_hint_count = 0
        async_count = 0
        docstring_count = 0
        
        for file_path in files[:50]:  # Sample first 50 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analyze naming conventions
                if re.search(r'def [a-z_][a-z0-9_]*\(', content):
                    snake_case_count += 1
                if re.search(r'def [A-Z][a-zA-Z0-9]*\(', content):
                    camel_case_count += 1
                
                # Analyze type hints
                if re.search(r'-> [A-Za-z]', content):
                    type_hint_count += 1
                
                # Analyze async usage
                if 'async def' in content:
                    async_count += 1
                
                # Analyze docstrings
                if '"""' in content or "'''" in content:
                    docstring_count += 1
                    
            except Exception as e:
                continue
        
        # Update conventions based on analysis
        if snake_case_count > camel_case_count:
            conventions["naming_style"] = "snake_case"
        else:
            conventions["naming_style"] = "camel_case"
        
        conventions["type_hints"] = type_hint_count > len(files) * 0.3
        conventions["async_usage"] = async_count > 0
        conventions["docstring_style"] = "google" if docstring_count > len(files) * 0.5 else "none"
    
    async def _analyze_dependency_graph(self):
        """Analyze dependency graph"""
        print("🔗 Analyzing dependency graph...")
        
        # Build dependency graph
        python_files = list(self.project_root.rglob("*.py"))
        for file_path in python_files:
            try:
                await self._analyze_file_dependencies(file_path)
            except Exception as e:
                continue
        
        # Convert to context format
        self.context.dependency_graph = dict(self.dependency_graph.adjacency())
    
    async def _analyze_file_dependencies(self, file_path: Path):
        """Analyze file dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Add to dependency graph
            file_name = str(file_path.relative_to(self.project_root))
            self.dependency_graph.add_node(file_name)
            
            for imp in imports:
                if imp.startswith('agentdev') or imp.startswith('stillme'):
                    self.dependency_graph.add_edge(file_name, imp)
                    
        except Exception as e:
            pass
    
    async def _analyze_business_goals(self):
        """Analyze business goals from documentation"""
        print("🎯 Analyzing business goals...")
        
        goals = []
        
        # Read README files
        readme_files = list(self.project_root.rglob("README.md"))
        for readme in readme_files:
            try:
                with open(readme, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract goals from content
                if "AI" in content or "agent" in content.lower():
                    goals.append("AI-powered automation")
                if "enterprise" in content.lower():
                    goals.append("Enterprise-grade solution")
                if "security" in content.lower():
                    goals.append("Security-first approach")
                if "scalability" in content.lower():
                    goals.append("Scalable architecture")
                    
            except Exception as e:
                continue
        
        self.context.business_goals = list(set(goals))
    
    async def _analyze_technical_constraints(self):
        """Analyze technical constraints"""
        print("⚙️ Analyzing technical constraints...")
        
        constraints = []
        
        # Check for specific constraints
        if (self.project_root / "requirements.txt").exists():
            constraints.append("Python dependency management")
        
        if (self.project_root / "Dockerfile").exists():
            constraints.append("Containerized deployment")
        
        if (self.project_root / ".github").exists():
            constraints.append("GitHub Actions CI/CD")
        
        if (self.project_root / "agentdev").exists():
            constraints.append("Microservices architecture")
        
        self.context.technical_constraints = constraints
    
    async def _analyze_team_preferences(self):
        """Analyze team preferences"""
        print("👥 Analyzing team preferences...")
        
        preferences = {
            "testing_framework": "pytest",
            "code_style": "black",
            "type_checking": "mypy",
            "documentation": "markdown",
            "version_control": "git"
        }
        
        # Detect preferences from project files
        if (self.project_root / "pytest.ini").exists():
            preferences["testing_framework"] = "pytest"
        
        if (self.project_root / "pyproject.toml").exists():
            preferences["build_system"] = "poetry"
        
        if (self.project_root / "Makefile").exists():
            preferences["build_tool"] = "make"
        
        self.context.team_preferences = preferences
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get context summary"""
        return {
            "project_name": self.context.project_name,
            "architecture": self.context.architecture_pattern,
            "language": self.context.language,
            "framework": self.context.framework,
            "dependencies": len(self.context.dependency_graph),
            "goals": len(self.context.business_goals),
            "constraints": len(self.context.technical_constraints),
            "conventions": self.context.coding_conventions
        }
    
    def export_context(self, output_path: str):
        """Export context to file"""
        context_data = {
            "context": asdict(self.context),
            "dependency_graph": dict(self.dependency_graph.adjacency()),
            "summary": self.get_context_summary()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Context exported to {output_path}")

# Example usage
async def main():
    """Example usage of ContextAnalyzer"""
    analyzer = ContextAnalyzer(".")
    context = await analyzer.analyze_project()
    
    print("🎯 Project Context Analysis Results:")
    print(f"Project: {context.project_name}")
    print(f"Architecture: {context.architecture_pattern}")
    print(f"Language: {context.language}")
    print(f"Framework: {context.framework}")
    print(f"Dependencies: {len(context.dependency_graph)}")
    print(f"Goals: {context.business_goals}")
    print(f"Constraints: {context.technical_constraints}")
    
    # Export context
    analyzer.export_context("reports/project_context.json")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
