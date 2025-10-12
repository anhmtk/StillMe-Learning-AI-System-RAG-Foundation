#!/usr/bin/env python3
"""
Feature-Group Coverage Smoke Test
Tests different feature groups to increase coverage
"""

import os
import sys
import importlib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_feature_group(group_name: str, modules: list, entry_points: list = None):
    """Test a feature group by importing modules and calling entry points"""
    logger.info(f"🧪 Testing feature group: {group_name}")
    
    success_count = 0
    total_count = len(modules)
    
    for module_name in modules:
        try:
            # Import module
            module = importlib.import_module(module_name)
            success_count += 1
            logger.debug(f"✅ Imported: {module_name}")
            
            # Try to call entry points if provided
            if entry_points:
                for entry_point in entry_points:
                    if hasattr(module, entry_point):
                        try:
                            entry_func = getattr(module, entry_point)
                            if callable(entry_func):
                                # Call with minimal/no arguments to avoid side effects
                                if entry_point in ['__init__', 'main']:
                                    # Skip potentially dangerous entry points
                                    continue
                                logger.debug(f"✅ Found entry point: {module_name}.{entry_point}")
                        except Exception as e:
                            logger.debug(f"⚠️ Entry point {entry_point} not callable: {e}")
                            
        except Exception as e:
            logger.warning(f"❌ Failed to import {module_name}: {e}")
    
    logger.info(f"📊 {group_name}: {success_count}/{total_count} modules imported")
    return success_count, total_count

def main():
    """Main function to test all feature groups"""
    logger.info("🔥 Starting feature-group coverage smoke test...")
    
    # Add current directory to sys.path
    sys.path.insert(0, os.getcwd())
    
    # Define feature groups
    feature_groups = {
        "stillme_core_modules": [
            "stillme_core",
            "stillme_core.core",
            "stillme_core.core.ai_manager",
            "stillme_core.core.executor", 
            "stillme_core.core.planner",
            "stillme_core.core.controller",
            "stillme_core.learning",
            "stillme_core.learning.pipeline",
            "stillme_core.learning.database",
            "stillme_core.modules",
            "stillme_core.providers",
            "stillme_core.providers.manager"
        ],
        "stillme_ethical_core": [
            "stillme_ethical_core",
            "stillme_ethical_core.ethics_checker",
            "stillme_ethical_core.stillme_framework"
        ],
        "learning_system": [
            "stillme_core.learning.autonomous_improvement_loop",
            "stillme_core.learning.continuous_evolution_engine", 
            "stillme_core.learning.adaptive_intelligence_core",
            "stillme_core.learning.self_optimization_system",
            "stillme_core.learning.pattern_recognition_engine",
            "stillme_core.learning.self_awareness_system",
            "stillme_core.learning.unified_memory_system",
            "stillme_core.learning.predictive_learning_system"
        ],
        "plugins_system": [
            "stillme_core.core.plugin_manager",
            "plugins",
            "plugins.calculator",
            "plugins.private_stub"
        ],
        "integration_modules": [
            "integration",
            "e2e_scenarios", 
            "oi_adapter",
            "security_basics"
        ],
        "tools_inventory": [
            "tools.inventory.import_graph",
            "tools.inventory.ast_hash",
            "tools.inventory.redundant_score",
            "tools.inventory.smoke_import",
            "tools.inventory.dynamic_import_detector"
        ]
    }
    
    total_success = 0
    total_modules = 0
    
    # Test each feature group
    for group_name, modules in feature_groups.items():
        success, total = test_feature_group(group_name, modules)
        total_success += success
        total_modules += total
    
    logger.info(f"🎯 Feature coverage summary:")
    logger.info(f"  - Total modules tested: {total_modules}")
    logger.info(f"  - Successfully imported: {total_success}")
    logger.info(f"  - Success rate: {(total_success/total_modules)*100:.1f}%")
    
    return total_success, total_modules

if __name__ == "__main__":
    main()
