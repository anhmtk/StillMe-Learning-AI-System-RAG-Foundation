#!/usr/bin/env python3
"""
Generate StillMe Structural Manifest

This script scans the validation system and generates a structural manifest
that StillMe can use to understand its own architecture.

The manifest is designed to be consumed by the RAG system as foundational knowledge.
"""

import json
import ast
import inspect
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.validation import (
    CitationRequired, CitationRelevance, EvidenceOverlap, NumericUnitsBasic,
    SchemaFormat, EthicsAdapter, ConfidenceValidator, FallbackHandler,
    ReviewAdapter, LanguageValidator, IdentityCheckValidator,
    EgoNeutralityValidator, SourceConsensusValidator, PhilosophicalDepthValidator,
    HallucinationExplanationValidator, VerbosityValidator, FactualHallucinationValidator,
    ReligiousChoiceValidator, AISelfModelValidator
)
from stillme_core.validation.chain import ValidationEngine


def extract_validator_info(validator_class) -> Dict[str, Any]:
    """Extract information about a validator class"""
    validator_name = validator_class.__name__
    
    # Get docstring
    docstring = inspect.getdoc(validator_class) or ""
    
    # Try to get file path
    try:
        file_path = inspect.getfile(validator_class)
        # Make path relative to project root
        if project_root.as_posix() in file_path:
            file_path = file_path.replace(project_root.as_posix(), "").lstrip("/")
    except:
        file_path = "unknown"
    
    # Check if it's in parallel_safe or sequential_only
    # This is defined in ValidationEngine._can_run_parallel
    sequential_only = {
        "LanguageValidator",
        "CitationRequired",
        "CitationRelevance",
        "SourceConsensusValidator",
        "ConfidenceValidator",
        "FactualHallucinationValidator",
        "ReligiousChoiceValidator",
    }
    
    parallel_safe = {
        "EvidenceOverlap",
        "NumericUnitsBasic",
        "SchemaFormat",
        "EgoNeutralityValidator",
        "IdentityCheckValidator",
        "PhilosophicalDepthValidator",
        "EthicsAdapter",
        "HallucinationExplanationValidator",
        "VerbosityValidator",
    }
    
    # Determine criticality and execution mode
    if validator_name in sequential_only:
        execution_mode = "sequential"
        criticality = "High" if validator_name in ["LanguageValidator", "CitationRequired", "ConfidenceValidator"] else "Medium"
    elif validator_name in parallel_safe:
        execution_mode = "parallel"
        criticality = "Medium"
    else:
        execution_mode = "sequential"  # Default for safety
        criticality = "Medium"
    
    # Special cases for criticality
    if validator_name == "LanguageValidator":
        criticality = "Blocker"  # Must run first
    elif validator_name in ["CitationRequired", "ConfidenceValidator", "FactualHallucinationValidator"]:
        criticality = "High"
    elif validator_name == "EthicsAdapter":
        criticality = "High"  # Blocks harmful content
    
    # Extract purpose from docstring (first sentence)
    purpose = docstring.split('.')[0] if docstring else f"Validates {validator_name.lower()}"
    
    return {
        "name": validator_name,
        "purpose": purpose,
        "docstring": docstring,
        "criticality": criticality,
        "execution_mode": execution_mode,
        "parallel_safe": validator_name in parallel_safe,
        "file_path": file_path,
    }


def determine_validator_layers() -> List[Dict[str, Any]]:
    """Determine logical layers for validators"""
    layers = [
        {
            "layer": 1,
            "name": "Language & Format",
            "description": "Ensures output language consistency and basic format",
            "members": ["LanguageValidator", "SchemaFormat"]
        },
        {
            "layer": 2,
            "name": "Citation & Evidence",
            "description": "Validates citations and evidence overlap with RAG context",
            "members": ["CitationRequired", "CitationRelevance", "EvidenceOverlap"]
        },
        {
            "layer": 3,
            "name": "Content Quality",
            "description": "Validates factual accuracy, confidence, and content quality",
            "members": ["ConfidenceValidator", "FactualHallucinationValidator", "NumericUnitsBasic"]
        },
        {
            "layer": 4,
            "name": "Identity & Ethics",
            "description": "Ensures StillMe identity consistency and ethical compliance",
            "members": ["IdentityCheckValidator", "EgoNeutralityValidator", "EthicsAdapter", "ReligiousChoiceValidator"]
        },
        {
            "layer": 5,
            "name": "Source Consensus",
            "description": "Detects contradictions between multiple sources",
            "members": ["SourceConsensusValidator"]
        },
        {
            "layer": 6,
            "name": "Specialized Validation",
            "description": "Domain-specific and advanced validators",
            "members": ["PhilosophicalDepthValidator", "HallucinationExplanationValidator", 
                       "VerbosityValidator", "AISelfModelValidator"]
        },
        {
            "layer": 7,
            "name": "Fallback & Review",
            "description": "Handles validation failures and provides review mechanisms",
            "members": ["FallbackHandler", "ReviewAdapter"]
        }
    ]
    return layers


def calculate_validation_logic_hash(validators: List) -> str:
    """
    Calculate hash of validation logic by reading source code of all validators.
    This hash changes whenever any validator's logic is modified.
    """
    validation_dir = project_root / "stillme_core" / "validation"
    hash_input = []
    
    # Read source code of all validator files
    validator_files = set()
    for validator_class in validators:
        try:
            file_path = Path(inspect.getfile(validator_class))
            if file_path.exists():
                validator_files.add(file_path)
        except:
            pass
    
    # Also check chain.py for validation orchestration logic
    chain_file = validation_dir / "chain.py"
    if chain_file.exists():
        validator_files.add(chain_file)
    
    # Read and hash each file
    for file_path in sorted(validator_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Include full content (including docstrings) to detect any changes
                hash_input.append(f"{file_path.relative_to(project_root)}:{content}")
        except Exception as e:
            # If file can't be read, include error in hash
            hash_input.append(f"{file_path}:ERROR:{str(e)}")
    
    # Calculate SHA256 hash
    combined = "\n".join(hash_input)
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return hash_obj.hexdigest()[:16]  # Use first 16 chars for readability


def generate_manifest() -> Dict[str, Any]:
    """Generate the complete structural manifest"""
    
    # Get all validator classes
    validators = [
        CitationRequired, CitationRelevance, EvidenceOverlap, NumericUnitsBasic,
        SchemaFormat, EthicsAdapter, ConfidenceValidator, FallbackHandler,
        ReviewAdapter, LanguageValidator, IdentityCheckValidator,
        EgoNeutralityValidator, SourceConsensusValidator, PhilosophicalDepthValidator,
        HallucinationExplanationValidator, VerbosityValidator, FactualHallucinationValidator,
        ReligiousChoiceValidator, AISelfModelValidator
    ]
    
    # Calculate validation logic hash
    validation_logic_hash = calculate_validation_logic_hash(validators)
    
    # Extract info for each validator
    registry = {}
    for validator_class in validators:
        info = extract_validator_info(validator_class)
        registry[info["name"]] = {
            "purpose": info["purpose"],
            "criticality": info["criticality"],
            "execution_mode": info["execution_mode"],
            "parallel_safe": info["parallel_safe"],
            "file_path": info["file_path"],
            "docstring": info["docstring"][:200] + "..." if len(info["docstring"]) > 200 else info["docstring"]
        }
    
    # Determine which validators are always active vs conditional
    always_active = [
        "LanguageValidator", "CitationRequired", "CitationRelevance", "NumericUnitsBasic",
        "ConfidenceValidator", "FactualHallucinationValidator", "ReligiousChoiceValidator",
        "HallucinationExplanationValidator", "VerbosityValidator", "EthicsAdapter"
    ]
    
    conditional = [
        "EvidenceOverlap",  # Only when has context
        "SourceConsensusValidator",  # Only when has >=2 sources
        "EgoNeutralityValidator",  # Only when has context
        "IdentityCheckValidator",  # Only when enabled
        "PhilosophicalDepthValidator",  # Only for philosophical questions
        "ReviewAdapter",  # May not always be used
        "AISelfModelValidator",  # Only for AI_SELF_MODEL domain
    ]
    
    # Count active validators (minimum when no context, maximum when all conditions met)
    min_validators = len(always_active)
    max_validators = len(always_active) + len(conditional)
    
    # Determine layers
    layers = determine_validator_layers()
    
    manifest = {
        "system_name": "StillMe",
        "version": "1.2.0",
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "validation_framework": {
            "total_validators": len(validators),
            "min_active_validators": min_validators,
            "max_active_validators": max_validators,
            "always_active": always_active,
            "conditional": conditional,
            "layers": layers,
            "registry": registry,
            "validation_logic_hash": validation_logic_hash,
            "validation_logic_hash_updated": datetime.now(timezone.utc).isoformat()
        },
        "metadata": {
            "generated_by": "scripts/generate_manifest.py",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "This manifest is automatically generated from the codebase. It should be regenerated whenever validators are added, removed, or modified. The validation_logic_hash changes whenever any validator's source code changes."
        }
    }
    
    return manifest


def main():
    """Main function to generate and save manifest"""
    print("🔍 Scanning StillMe validation system...")
    
    try:
        manifest = generate_manifest()
        
        # Save to data directory (accessible by RAG system)
        output_dir = project_root / "data"
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / "stillme_manifest.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Manifest generated successfully: {output_path}")
        print(f"   - Total validators: {manifest['validation_framework']['total_validators']}")
        print(f"   - Active validators: {manifest['validation_framework']['min_active_validators']}-{manifest['validation_framework']['max_active_validators']}")
        print(f"   - Layers: {len(manifest['validation_framework']['layers'])}")
        
        return 0
    except Exception as e:
        print(f"❌ Error generating manifest: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

