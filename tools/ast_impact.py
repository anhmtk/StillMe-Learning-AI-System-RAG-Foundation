"""AST Impact Analysis Tools"""

import ast
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class ASTImpact:
    """AST impact analysis result"""
    node_type: str
    impact_level: str
    description: str
    line_number: int
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ASTImpactAnalyzer:
    """AST impact analyzer"""

    def __init__(self):
        self.logger = logger
        self.logger.info("✅ ASTImpactAnalyzer initialized")

    def analyze_code_impact(self, code: str) -> list[ASTImpact]:
        """Analyze code impact using AST"""
        try:
            tree = ast.parse(code)
            impacts = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    impacts.append(ASTImpact(
                        node_type="FunctionDef",
                        impact_level="medium",
                        description=f"Function definition: {node.name}",
                        line_number=node.lineno
                    ))
                elif isinstance(node, ast.ClassDef):
                    impacts.append(ASTImpact(
                        node_type="ClassDef",
                        impact_level="high",
                        description=f"Class definition: {node.name}",
                        line_number=node.lineno
                    ))
                elif isinstance(node, ast.Import):
                    impacts.append(ASTImpact(
                        node_type="Import",
                        impact_level="low",
                        description="Import statement",
                        line_number=node.lineno
                    ))

            self.logger.info(f"🔍 AST analysis completed: {len(impacts)} impacts found")
            return impacts

        except SyntaxError as e:
            self.logger.error(f"❌ AST analysis failed - syntax error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ AST analysis failed: {e}")
            return []

    def get_impact_summary(self, impacts: list[ASTImpact]) -> dict[str, Any]:
        """Get impact summary"""
        try:
            impact_counts = {}
            for impact in impacts:
                level = impact.impact_level
                impact_counts[level] = impact_counts.get(level, 0) + 1

            return {
                "total_impacts": len(impacts),
                "impact_by_level": impact_counts,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get impact summary: {e}")
            return {"error": str(e)}
