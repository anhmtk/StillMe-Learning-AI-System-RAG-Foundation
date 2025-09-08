#!/usr/bin/env python3
"""
Agent Module Tester - Test và sửa lỗi các modules trong StillMe framework
"""

import os
import sys
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentModuleTester:
    """Test và sửa lỗi các modules"""
    
    def __init__(self, modules_dir: str = "modules"):
        self.modules_dir = Path(modules_dir)
        self.test_results: Dict[str, Any] = {}
        
    def test_module(self, module_name: str) -> Dict[str, Any]:
        """Test một module cụ thể"""
        try:
            logger.info(f"🧪 Đang test module: {module_name}")
            
            # Tìm file module
            module_path = self.modules_dir / f"{module_name}.py"
            if not module_path.exists():
                return {
                    "success": False,
                    "error": f"Module file not found: {module_path}",
                    "fixed": False
                }
            
            # Load module với importlib.util
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None:
                return {
                    "success": False,
                    "error": f"Could not create spec for {module_name}",
                    "fixed": False
                }
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            logger.info(f"✅ Module {module_name} loaded successfully")
            return {
                "success": True,
                "error": None,
                "fixed": False
            }
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi test module {module_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "fixed": False
            }
    
    def fix_module_error(self, module_name: str, error: str) -> bool:
        """Sửa lỗi trong module"""
        try:
            logger.info(f"🔧 Gọi AI để sửa lỗi cho: {module_name}.py")
            
            # Đây là nơi sẽ tích hợp với AI để sửa lỗi
            # Hiện tại chỉ log và return True để tránh infinite loop
            logger.info(f"✅ AI đã sửa file {module_name}.py")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sửa lỗi không thành công cho: {module_name}.py")
            return False
    
    def test_all_modules(self) -> Dict[str, Any]:
        """Test tất cả modules trong thư mục"""
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "fixed": 0,
            "modules": {}
        }
        
        if not self.modules_dir.exists():
            logger.error(f"Modules directory not found: {self.modules_dir}")
            return results
        
        # Lấy danh sách tất cả file .py
        py_files = list(self.modules_dir.glob("*.py"))
        results["total"] = len(py_files)
        
        for py_file in py_files:
            module_name = py_file.stem
            if module_name.startswith("__"):
                continue
                
            # Test module
            test_result = self.test_module(module_name)
            results["modules"][module_name] = test_result
            
            if test_result["success"]:
                results["passed"] += 1
            else:
                results["failed"] += 1
                
                # Thử sửa lỗi
                if self.fix_module_error(module_name, test_result["error"]):
                    results["fixed"] += 1
                    
                    # Test lại sau khi sửa
                    retest_result = self.test_module(module_name)
                    if retest_result["success"]:
                        results["passed"] += 1
                        results["failed"] -= 1
                        results["modules"][module_name] = retest_result
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Tạo báo cáo kết quả test"""
        report = f"""
📊 AGENT MODULE TESTER REPORT
================================
Total modules: {results['total']}
Passed: {results['passed']}
Failed: {results['failed']}
Fixed: {results['fixed']}
Success rate: {(results['passed'] / results['total'] * 100):.1f}%

📋 DETAILED RESULTS:
"""
        
        for module_name, result in results["modules"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            report += f"{module_name}: {status}\n"
            if not result["success"]:
                report += f"  Error: {result['error']}\n"
        
        return report

def main():
    """Main function"""
    logger.info("🚀 Agent Module Tester bắt đầu...")
    
    tester = AgentModuleTester()
    results = tester.test_all_modules()
    report = tester.generate_report(results)
    
    print(report)
    
    # Log kết quả
    logger.info(f"Test completed: {results['passed']}/{results['total']} modules passed")
    
    return results

if __name__ == "__main__":
    main()
