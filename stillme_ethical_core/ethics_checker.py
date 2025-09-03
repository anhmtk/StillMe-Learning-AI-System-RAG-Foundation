import json
import logging
from typing import Dict, Any

logger = logging.getLogger('StillmeEthicalCore-EthicsChecker')
class EthicsChecker:
        def __init__(self, level: str = "medium"):
            self.level = level
            logger.info(f"EthicsChecker initialized with level: {self.level}")

        def check_plan(self, plan: Dict[str, Any]) -> bool:
            # Simplified ethics check for demonstration
            # In a real scenario, this would involve complex logic
            logger.info("Performing ethics check on plan...")
            # For this example, assume all plans are ethical unless they explicitly contain harmful keywords
            if "delete all files" in json.dumps(plan).lower(): # Example check
                logger.warning("Potential harmful action detected in plan!")
                return False
            return True