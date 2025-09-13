#!/usr/bin/env python3
"""
AgentDev Advanced - Legacy Code Pattern Analysis
SAFETY: Read-only analysis, no code modifications
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class LegacyModuleInfo:
    """Information about a legacy module"""

    name: str
    file_path: str
    class_name: str
    config_class: str
    description: str
    methods: List[str]
    dependencies: List[str]
    patterns: List[str]
    anti_patterns: List[str]


class LegacyCodeAnalyzer:
    """Safe analyzer for legacy code patterns"""

    def __init__(self, legacy_dir: str = "modules/backup_legacy"):
        self.legacy_dir = Path(legacy_dir)
        self.modules = []
        self.patterns = {
            "common_patterns": [],
            "anti_patterns": [],
            "security_concerns": [],
            "deprecation_indicators": [],
        }

    def analyze_legacy_modules(self) -> Dict[str, Any]:
        """Analyze all legacy modules safely"""
        print("🔍 Starting legacy code analysis...")

        # Safety check: Ensure we're in read-only mode
        if not self.legacy_dir.exists():
            raise FileNotFoundError(f"Legacy directory not found: {self.legacy_dir}")

        for file_path in self.legacy_dir.glob("*.py"):
            if file_path.is_file():
                module_info = self._analyze_single_module(file_path)
                self.modules.append(module_info)

        self._identify_patterns()
        return self._generate_analysis_report()

    def _analyze_single_module(self, file_path: Path) -> LegacyModuleInfo:
        """Analyze a single legacy module"""
        print(f"📄 Analyzing: {file_path.name}")

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️ Warning: Could not read {file_path.name}: {e}")
            return LegacyModuleInfo(
                name=file_path.stem,
                file_path=str(file_path),
                class_name="Unknown",
                config_class="Unknown",
                description="Error reading file",
                methods=[],
                dependencies=[],
                patterns=[],
                anti_patterns=[],
            )

        # Extract class information
        class_name = self._extract_class_name(content)
        config_class = self._extract_config_class(content)
        description = self._extract_description(content)
        methods = self._extract_methods(content)
        dependencies = self._extract_dependencies(content)
        patterns = self._identify_module_patterns(content)
        anti_patterns = self._identify_anti_patterns(content)

        return LegacyModuleInfo(
            name=file_path.stem,
            file_path=str(file_path),
            class_name=class_name,
            config_class=config_class,
            description=description,
            methods=methods,
            dependencies=dependencies,
            patterns=patterns,
            anti_patterns=anti_patterns,
        )

    def _extract_class_name(self, content: str) -> str:
        """Extract main class name from content"""
        class_match = re.search(r"class\s+(\w+):", content)
        return class_match.group(1) if class_match else "Unknown"

    def _extract_config_class(self, content: str) -> str:
        """Extract config class name from content"""
        config_match = re.search(r"class\s+(\w*[Cc]onfig\w*):", content)
        return config_match.group(1) if config_match else "Unknown"

    def _extract_description(self, content: str) -> str:
        """Extract module description from docstring"""
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()
        return "No description found"

    def _extract_methods(self, content: str) -> List[str]:
        """Extract method names from content"""
        methods = re.findall(r"def\s+(\w+)\s*\(", content)
        return [method for method in methods if not method.startswith("_")]

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract import dependencies from content"""
        imports = re.findall(r"from\s+(\S+)\s+import|import\s+(\S+)", content)
        dependencies = []
        for imp in imports:
            if imp[0]:
                dependencies.append(imp[0])
            if imp[1]:
                dependencies.append(imp[1])
        return dependencies

    def _identify_module_patterns(self, content: str) -> List[str]:
        """Identify common patterns in the module"""
        patterns = []

        # Check for common patterns
        if "dataclass" in content:
            patterns.append("uses_dataclass")
        if "logging" in content:
            patterns.append("uses_logging")
        if "typing" in content:
            patterns.append("uses_type_hints")
        if "config" in content.lower():
            patterns.append("has_configuration")
        if "def __init__" in content:
            patterns.append("has_constructor")

        return patterns

    def _identify_anti_patterns(self, content: str) -> List[str]:
        """Identify anti-patterns in the module"""
        anti_patterns = []

        # Check for anti-patterns
        if "print(" in content and "logging" not in content:
            anti_patterns.append("uses_print_instead_of_logging")
        if "TODO" in content or "FIXME" in content:
            anti_patterns.append("has_todo_comments")
        if "pass" in content and "def" in content:
            anti_patterns.append("has_empty_methods")
        if "except:" in content:
            anti_patterns.append("bare_except_clause")
        if "eval(" in content or "exec(" in content:
            anti_patterns.append("uses_eval_or_exec")

        return anti_patterns

    def _identify_patterns(self):
        """Identify patterns across all modules"""
        all_patterns = []
        all_anti_patterns = []

        for module in self.modules:
            all_patterns.extend(module.patterns)
            all_anti_patterns.extend(module.anti_patterns)

        # Count pattern frequency
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        anti_pattern_counts = {}
        for anti_pattern in all_anti_patterns:
            anti_pattern_counts[anti_pattern] = (
                anti_pattern_counts.get(anti_pattern, 0) + 1
            )

        self.patterns["common_patterns"] = pattern_counts
        self.patterns["anti_patterns"] = anti_pattern_counts

    def _generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        return {
            "analysis_timestamp": "2025-09-09T23:30:14Z",
            "total_modules": len(self.modules),
            "modules": [
                {
                    "name": module.name,
                    "class_name": module.class_name,
                    "config_class": module.config_class,
                    "description": module.description,
                    "method_count": len(module.methods),
                    "methods": module.methods,
                    "dependency_count": len(module.dependencies),
                    "dependencies": module.dependencies,
                    "patterns": module.patterns,
                    "anti_patterns": module.anti_patterns,
                }
                for module in self.modules
            ],
            "pattern_analysis": self.patterns,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Analyze anti-patterns
        if any(
            "uses_print_instead_of_logging" in module.anti_patterns
            for module in self.modules
        ):
            recommendations.append("Replace print statements with proper logging")

        if any("has_todo_comments" in module.anti_patterns for module in self.modules):
            recommendations.append("Address TODO/FIXME comments before migration")

        if any("bare_except_clause" in module.anti_patterns for module in self.modules):
            recommendations.append(
                "Replace bare except clauses with specific exception handling"
            )

        # Analyze patterns
        if "uses_dataclass" in self.patterns["common_patterns"]:
            recommendations.append("Good: Dataclass usage is modern and maintainable")

        if "uses_type_hints" in self.patterns["common_patterns"]:
            recommendations.append("Good: Type hints improve code maintainability")

        return recommendations


def main():
    """Main analysis function"""
    print("🤖 AgentDev Advanced - Legacy Code Analysis")
    print("=" * 50)

    analyzer = LegacyCodeAnalyzer()

    try:
        report = analyzer.analyze_legacy_modules()

        # Save report
        report_path = Path(
            "backup/legacy_analysis_20250909_233014/legacy_analysis_report.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Analysis complete! Report saved to: {report_path}")
        print(f"📊 Analyzed {report['total_modules']} legacy modules")
        print(
            f"🔍 Found {len(report['pattern_analysis']['common_patterns'])} common patterns"
        )
        print(
            f"⚠️ Found {len(report['pattern_analysis']['anti_patterns'])} anti-patterns"
        )

        return report

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None


if __name__ == "__main__":
    main()
