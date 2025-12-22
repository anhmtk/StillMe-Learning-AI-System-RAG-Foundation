"""
Instruction Loader for Configuration-Driven Prompt Builder

Loads instructions from YAML config files instead of hardcoding in Python.
This makes instructions maintainable, testable, and scalable.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Base path for instruction configs
INSTRUCTIONS_DIR = Path(__file__).parent / "instructions"


class InstructionLoader:
    """Loads and caches instructions from YAML config files"""
    
    def __init__(self, instructions_dir: Optional[Path] = None):
        """
        Initialize instruction loader
        
        Args:
            instructions_dir: Directory containing YAML instruction files (default: backend/identity/instructions)
        """
        self.instructions_dir = instructions_dir or INSTRUCTIONS_DIR
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Ensure instructions directory exists
        if not self.instructions_dir.exists():
            logger.warning(f"Instructions directory does not exist: {self.instructions_dir}")
            self.instructions_dir.mkdir(parents=True, exist_ok=True)
    
    @lru_cache(maxsize=128)
    def load_instruction(self, instruction_name: str) -> Optional[Dict[str, Any]]:
        """
        Load instruction from YAML file
        
        Args:
            instruction_name: Name of instruction (e.g., "validator_count")
            
        Returns:
            Instruction dict with keys: detection, instruction, metadata
            Returns None if file not found or invalid
        """
        # Check cache first
        if instruction_name in self._cache:
            return self._cache[instruction_name]
        
        # Load from YAML file
        yaml_path = self.instructions_dir / f"{instruction_name}.yaml"
        
        if not yaml_path.exists():
            logger.warning(f"Instruction file not found: {yaml_path}")
            return None
        
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                instruction_data = yaml.safe_load(f)
            
            if not isinstance(instruction_data, dict):
                logger.error(f"Invalid instruction format in {yaml_path}: expected dict")
                return None
            
            # Cache and return
            self._cache[instruction_name] = instruction_data
            logger.debug(f"Loaded instruction: {instruction_name} from {yaml_path}")
            return instruction_data
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading instruction {instruction_name}: {e}")
            return None
    
    def get_instruction_text(self, instruction_name: str, lang: str = "vi") -> Optional[str]:
        """
        Get instruction text for specific language
        
        Args:
            instruction_name: Name of instruction
            lang: Language code (default: "vi")
            
        Returns:
            Instruction text string, or None if not found
        """
        instruction_data = self.load_instruction(instruction_name)
        if not instruction_data:
            return None
        
        instruction_section = instruction_data.get("instruction", {})
        if not isinstance(instruction_section, dict):
            return None
        
        return instruction_section.get(lang) or instruction_section.get("en")
    
    def get_detection_patterns(self, instruction_name: str) -> list:
        """
        Get detection patterns for instruction
        
        Args:
            instruction_name: Name of instruction
            
        Returns:
            List of regex patterns for detection
        """
        instruction_data = self.load_instruction(instruction_name)
        if not instruction_data:
            return []
        
        detection = instruction_data.get("detection", {})
        if not isinstance(detection, dict):
            return []
        
        return detection.get("patterns", [])
    
    def get_priority(self, instruction_name: str) -> str:
        """
        Get priority level for instruction
        
        Args:
            instruction_name: Name of instruction
            
        Returns:
            Priority string (e.g., "P1_CRITICAL")
        """
        instruction_data = self.load_instruction(instruction_name)
        if not instruction_data:
            return "P4_LOW"
        
        detection = instruction_data.get("detection", {})
        if not isinstance(detection, dict):
            return "P4_LOW"
        
        return detection.get("priority", "P4_LOW")
    
    def get_metadata(self, instruction_name: str) -> Dict[str, Any]:
        """
        Get metadata for instruction
        
        Args:
            instruction_name: Name of instruction
            
        Returns:
            Metadata dict
        """
        instruction_data = self.load_instruction(instruction_name)
        if not instruction_data:
            return {}
        
        return instruction_data.get("metadata", {})
    
    def clear_cache(self):
        """Clear instruction cache (useful for testing or hot-reload)"""
        self._cache.clear()
        self.load_instruction.cache_clear()
        logger.info("Instruction cache cleared")


# Singleton instance
_loader_instance: Optional[InstructionLoader] = None


def get_instruction_loader() -> InstructionLoader:
    """Get singleton instruction loader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = InstructionLoader()
    return _loader_instance

