import json
import logging
from typing import Any

logger = logging.getLogger("StillmeEthicalCore-EthicsChecker")


class EthicsChecker:
    def __init__(self, level: str = "medium"):
        self.level = level
        logger.info(f"EthicsChecker initialized with level: {self.level}")

    def check_plan(self, plan: dict[str, Any]) -> bool:
        # Simplified ethics check for demonstration
        # In a real scenario, this would involve complex logic
        logger.info("Performing ethics check on plan...")
        # For this example, assume all plans are ethical unless they explicitly contain harmful keywords
        if "delete all files" in json.dumps(plan).lower():  # Example check
            logger.warning("Potential harmful action detected in plan!")
            return False
        return True

    def assess_framework_safety(self, old_code: str, new_code: str) -> bool:
        """Assess if new code is safe for framework"""
        logger.info("Assessing framework safety...")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "subprocess.run(",
            "subprocess.Popen(",
            "os.system(",
            "eval(",
            "exec(",
            "__import__(",
            "open(",
            "file(",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in new_code:
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                return False
        
        # Check if new code removes too much
        if len(new_code) < len(old_code) * 0.1:  # Less than 10% of original
            logger.warning("New code removes too much content")
            return False
            
        return True