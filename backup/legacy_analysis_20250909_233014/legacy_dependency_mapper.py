#!/usr/bin/env python3
"""
AgentDev Advanced - Legacy Dependency Mapping
SAFETY: Read-only analysis, creates dependency visualization
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import networkx as nx


class LegacyDependencyMapper:
    """Maps dependencies between legacy modules and current system"""

    def __init__(self, legacy_report_path: str):
        self.legacy_report_path = Path(legacy_report_path)
        self.current_modules = self._scan_current_modules()
        self.legacy_data = self._load_legacy_report()
        self.dependency_graph = nx.DiGraph()

    def _scan_current_modules(self) -> Dict[str, Any]:
        """Scan current modules directory for comparison"""
        current_modules = {}
        modules_dir = Path("modules")

        if modules_dir.exists():
            for file_path in modules_dir.rglob("*.py"):
                if "backup_legacy" not in str(file_path):
                    module_name = file_path.stem
                    current_modules[module_name] = {
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                    }

        return current_modules

    def _load_legacy_report(self) -> Dict[str, Any]:
        """Load legacy analysis report"""
        with open(self.legacy_report_path, encoding="utf-8") as f:
            return json.load(f)

    def create_dependency_map(self) -> Dict[str, Any]:
        """Create comprehensive dependency mapping"""
        print("🗺️ Creating legacy dependency map...")

        # Add legacy modules to graph
        for module in self.legacy_data["modules"]:
            self.dependency_graph.add_node(
                f"legacy_{module['name']}",
                type="legacy",
                class_name=module["class_name"],
                methods=module["methods"],
                dependencies=module["dependencies"],
            )

        # Add current modules to graph
        for module_name, module_info in self.current_modules.items():
            self.dependency_graph.add_node(
                f"current_{module_name}",
                type="current",
                path=module_info["path"],
                size=module_info["size"],
            )

        # Create potential migration mappings
        migration_mappings = self._create_migration_mappings()

        # Generate dependency analysis
        dependency_analysis = self._analyze_dependencies()

        return {
            "migration_mappings": migration_mappings,
            "dependency_analysis": dependency_analysis,
            "graph_stats": {
                "total_nodes": self.dependency_graph.number_of_nodes(),
                "total_edges": self.dependency_graph.number_of_edges(),
                "legacy_nodes": len(
                    [
                        n
                        for n in self.dependency_graph.nodes()
                        if n.startswith("legacy_")
                    ]
                ),
                "current_nodes": len(
                    [
                        n
                        for n in self.dependency_graph.nodes()
                        if n.startswith("current_")
                    ]
                ),
            },
        }

    def _create_migration_mappings(self) -> List[Dict[str, Any]]:
        """Create potential migration mappings between legacy and current modules"""
        mappings = []

        # Define potential mappings based on naming and functionality
        potential_mappings = {
            "conversational_core": ["conversational_core_v1", "conversational_core_v2"],
            "layered_memory": ["layered_memory_v1", "secure_memory_manager"],
            "smart_g_p_t__a_p_i__manager": [
                "unified_api_manager",
                "api_provider_manager",
            ],
            "token_optimizer": ["token_optimizer", "prompt_optimizer"],
        }

        for legacy_module in self.legacy_data["modules"]:
            legacy_name = legacy_module["name"]
            potential_targets = potential_mappings.get(legacy_name, [])

            # Check if potential targets exist in current modules
            existing_targets = []
            for target in potential_targets:
                if target in self.current_modules:
                    existing_targets.append(target)

            mapping = {
                "legacy_module": legacy_name,
                "legacy_class": legacy_module["class_name"],
                "potential_targets": existing_targets,
                "migration_complexity": self._assess_migration_complexity(
                    legacy_module
                ),
                "recommendations": self._generate_migration_recommendations(
                    legacy_module, existing_targets
                ),
            }

            mappings.append(mapping)

        return mappings

    def _assess_migration_complexity(self, legacy_module: Dict[str, Any]) -> str:
        """Assess migration complexity for a legacy module"""
        complexity_score = 0

        # Factor in method count
        if legacy_module["method_count"] > 10:
            complexity_score += 2
        elif legacy_module["method_count"] > 5:
            complexity_score += 1

        # Factor in dependencies
        if legacy_module["dependency_count"] > 5:
            complexity_score += 2
        elif legacy_module["dependency_count"] > 2:
            complexity_score += 1

        # Factor in anti-patterns
        complexity_score += len(legacy_module["anti_patterns"])

        if complexity_score >= 4:
            return "HIGH"
        elif complexity_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_migration_recommendations(
        self, legacy_module: Dict[str, Any], targets: List[str]
    ) -> List[str]:
        """Generate migration recommendations"""
        recommendations = []

        if not targets:
            recommendations.append(
                "No direct equivalent found - consider creating new module"
            )
            recommendations.append(
                "Review functionality and integrate into existing modules"
            )
        else:
            recommendations.append(f"Migrate to existing module: {', '.join(targets)}")
            recommendations.append("Update method signatures to match current API")
            recommendations.append("Test compatibility with current system")

        # Add specific recommendations based on anti-patterns
        if "has_todo_comments" in legacy_module["anti_patterns"]:
            recommendations.append("Address TODO comments before migration")

        return recommendations

    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependencies between legacy and current modules"""
        analysis = {
            "shared_dependencies": [],
            "unique_legacy_dependencies": [],
            "unique_current_dependencies": [],
            "dependency_conflicts": [],
        }

        # Collect all dependencies
        legacy_deps = set()
        for module in self.legacy_data["modules"]:
            legacy_deps.update(module["dependencies"])

        # Analyze shared dependencies
        analysis["shared_dependencies"] = list(legacy_deps)

        # Check for potential conflicts
        for dep in legacy_deps:
            if dep in ["logging", "typing", "dataclasses"]:
                analysis["dependency_conflicts"].append(
                    {
                        "dependency": dep,
                        "issue": "Standard library - no conflict",
                        "severity": "LOW",
                    }
                )

        return analysis

    def generate_visualization(
        self,
        output_path: str = "backup/legacy_analysis_20250909_233014/dependency_map.png",
    ):
        """Generate dependency visualization (if matplotlib is available)"""
        try:
            plt.figure(figsize=(12, 8))

            # Position nodes
            pos = nx.spring_layout(self.dependency_graph, k=3, iterations=50)

            # Color nodes by type
            legacy_nodes = [
                n for n in self.dependency_graph.nodes() if n.startswith("legacy_")
            ]
            current_nodes = [
                n for n in self.dependency_graph.nodes() if n.startswith("current_")
            ]

            # Draw nodes
            nx.draw_networkx_nodes(
                self.dependency_graph,
                pos,
                nodelist=legacy_nodes,
                node_color="red",
                node_size=500,
                alpha=0.7,
                label="Legacy Modules",
            )

            nx.draw_networkx_nodes(
                self.dependency_graph,
                pos,
                nodelist=current_nodes,
                node_color="green",
                node_size=500,
                alpha=0.7,
                label="Current Modules",
            )

            # Draw edges
            nx.draw_networkx_edges(
                self.dependency_graph,
                pos,
                edge_color="gray",
                arrows=True,
                arrowsize=20,
                alpha=0.6,
            )

            # Draw labels
            nx.draw_networkx_labels(
                self.dependency_graph, pos, font_size=8, font_weight="bold"
            )

            plt.title("Legacy to Current Module Dependency Map")
            plt.legend()
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            print(f"📊 Dependency visualization saved to: {output_path}")

        except ImportError:
            print("⚠️ Matplotlib not available - skipping visualization")
        except Exception as e:
            print(f"⚠️ Visualization failed: {e}")


def main():
    """Main dependency mapping function"""
    print("🗺️ AgentDev Advanced - Legacy Dependency Mapping")
    print("=" * 50)

    report_path = "backup/legacy_analysis_20250909_233014/legacy_analysis_report.json"

    if not Path(report_path).exists():
        print(f"❌ Legacy report not found: {report_path}")
        return None

    mapper = LegacyDependencyMapper(report_path)

    try:
        dependency_map = mapper.create_dependency_map()

        # Save dependency map
        map_path = Path(
            "backup/legacy_analysis_20250909_233014/legacy_dependency_map.json"
        )
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(dependency_map, f, indent=2, ensure_ascii=False)

        print(f"✅ Dependency mapping complete! Map saved to: {map_path}")
        print(
            f"📊 Found {len(dependency_map['migration_mappings'])} migration mappings"
        )
        print(
            f"🔍 Analyzed {dependency_map['graph_stats']['total_nodes']} total modules"
        )

        # Generate visualization
        mapper.generate_visualization()

        return dependency_map

    except Exception as e:
        print(f"❌ Dependency mapping failed: {e}")
        return None


if __name__ == "__main__":
    main()
