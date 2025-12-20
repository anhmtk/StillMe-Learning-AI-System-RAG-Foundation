#!/usr/bin/env python3
"""
Inject StillMe Structural Manifest into RAG System

This script converts the generated manifest.json into a human-readable format
and injects it into ChromaDB as foundational knowledge with CRITICAL_FOUNDATION priority.
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from backend.vector_db.rag_retrieval import RAGRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def manifest_to_text(manifest: dict) -> str:
    """Convert manifest JSON to human-readable text format for RAG"""
    
    vf = manifest["validation_framework"]
    
    text = f"""# StillMe Structural Manifest - Validation Framework

**System**: {manifest['system_name']} v{manifest['version']}
**Last Sync**: {manifest['last_sync']}
**Generated**: {manifest['metadata']['generation_timestamp']}

## Validation Framework Overview

StillMe uses a **multi-layer validation framework** with **{vf['total_validators']} total validators**.

**Active Validators**: {vf['min_active_validators']}-{vf['max_active_validators']} validators run per response (depending on context and question type).

### Always Active Validators ({len(vf['always_active'])})

These validators run on every response:
"""
    
    for validator_name in vf['always_active']:
        validator_info = vf['registry'].get(validator_name, {})
        purpose = validator_info.get('purpose', 'N/A')
        criticality = validator_info.get('criticality', 'Medium')
        execution_mode = validator_info.get('execution_mode', 'sequential')
        text += f"\n- **{validator_name}**: {purpose} (Criticality: {criticality}, Execution: {execution_mode})"
    
    text += f"\n\n### Conditional Validators ({len(vf['conditional'])})"
    text += "\n\nThese validators run only when specific conditions are met:\n"
    
    for validator_name in vf['conditional']:
        validator_info = vf['registry'].get(validator_name, {})
        purpose = validator_info.get('purpose', 'N/A')
        criticality = validator_info.get('criticality', 'Medium')
        execution_mode = validator_info.get('execution_mode', 'sequential')
        text += f"\n- **{validator_name}**: {purpose} (Criticality: {criticality}, Execution: {execution_mode})"
    
    text += "\n\n## Validation Layers\n\n"
    text += "StillMe's validation framework is organized into 7 logical layers:\n\n"
    
    for layer in vf['layers']:
        layer_num = layer.get('layer', 'N/A')
        layer_name = layer.get('name', 'Unknown')
        description = layer.get('description', '')
        members = layer.get('members', [])
        
        text += f"### Layer {layer_num}: {layer_name}\n"
        text += f"{description}\n\n"
        text += "**Validators in this layer:**\n"
        for member in members:
            validator_info = vf['registry'].get(member, {})
            purpose = validator_info.get('purpose', 'N/A')
            text += f"- **{member}**: {purpose}\n"
        text += "\n"
    
    text += "\n## Complete Validator Registry\n\n"
    text += "Detailed information about each validator:\n\n"
    
    for validator_name, validator_info in sorted(vf['registry'].items()):
        text += f"### {validator_name}\n"
        text += f"- **Purpose**: {validator_info.get('purpose', 'N/A')}\n"
        text += f"- **Criticality**: {validator_info.get('criticality', 'Medium')}\n"
        text += f"- **Execution Mode**: {validator_info.get('execution_mode', 'sequential')}\n"
        text += f"- **Parallel Safe**: {validator_info.get('parallel_safe', False)}\n"
        text += f"- **File Path**: `{validator_info.get('file_path', 'unknown')}`\n"
        if validator_info.get('docstring'):
            docstring = validator_info['docstring']
            if len(docstring) > 300:
                docstring = docstring[:300] + "..."
            text += f"- **Description**: {docstring}\n"
        text += "\n"
    
    text += "\n## CRITICAL: Validator Count Information\n\n"
    text += f"**StillMe has exactly {vf['total_validators']} validators total.**\n\n"
    text += f"- **Minimum active**: {vf['min_active_validators']} validators (when no context available)\n"
    text += f"- **Maximum active**: {vf['max_active_validators']} validators (when all conditions are met)\n"
    text += f"- **Always active**: {len(vf['always_active'])} validators\n"
    text += f"- **Conditional**: {len(vf['conditional'])} validators\n\n"
    text += "**When asked about the number of validators, StillMe MUST say:**\n"
    text += f"- \"StillMe has {vf['total_validators']} validators total\"\n"
    text += f"- \"StillMe uses {vf['min_active_validators']}-{vf['max_active_validators']} validators per response depending on context\"\n"
    text += "- **DO NOT say \"15-layer\" or \"13+ validators\"** - these are outdated or incorrect\n\n"
    
    text += "## Execution Architecture\n\n"
    text += "StillMe's validation engine supports:\n"
    text += "- **Sequential execution**: Validators with dependencies run in order\n"
    text += "- **Parallel execution**: Independent validators run concurrently for performance\n"
    text += "- **Early exit**: Critical failures stop validation immediately\n"
    text += "- **Auto-patching**: Some validators can automatically fix issues\n\n"
    
    text += "## Notes\n\n"
    text += f"- This manifest was automatically generated by `{manifest['metadata']['generated_by']}`\n"
    text += "- The manifest should be regenerated whenever validators are added, removed, or modified\n"
    text += "- This is the **source of truth** for StillMe's validation framework structure\n"
    
    return text


def inject_manifest_to_rag():
    """Load manifest and inject into RAG system"""
    try:
        # Load manifest
        manifest_path = project_root / "data" / "stillme_manifest.json"
        
        if not manifest_path.exists():
            logger.error(f"❌ Manifest not found: {manifest_path}")
            logger.info("💡 Run 'python scripts/generate_manifest.py' first to generate the manifest")
            return False
        
        logger.info(f"📖 Loading manifest from {manifest_path}...")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Convert to text
        logger.info("📝 Converting manifest to text format...")
        manifest_text = manifest_to_text(manifest)
        
        logger.info(f"📊 Manifest text length: {len(manifest_text)} characters")
        
        # Initialize RAG components
        logger.info("🔧 Initializing RAG components...")
        chroma_client = ChromaClient(persist_directory="data/vector_db")
        embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        
        # Prepare metadata with CRITICAL_FOUNDATION priority
        tags_list = [
            "foundational:stillme",
            "CRITICAL_FOUNDATION",
            "stillme",
            "validation",
            "validators",
            "validation-chain",
            "structural-manifest",
            "system-architecture",
            "self-awareness"
        ]
        tags_string = ",".join(tags_list)
        
        logger.info("💾 Injecting manifest into RAG system...")
        
        success = rag_retrieval.add_learning_content(
            content=manifest_text,
            source="CRITICAL_FOUNDATION",
            content_type="knowledge",
            metadata={
                "title": "StillMe Structural Manifest - Validation Framework",
                "foundational": "stillme",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",
                "tags": tags_string,
                "importance_score": 1.0,  # Maximum importance
                "manifest_version": manifest["version"],
                "last_sync": manifest["last_sync"],
                "description": "CRITICAL: Structural manifest of StillMe's validation framework - source of truth for validator count and architecture. MUST be retrieved when answering about StillMe's validation chain."
            }
        )
        
        if success:
            logger.info("✅ Manifest injected successfully into RAG system!")
            logger.info(f"   - Total validators: {manifest['validation_framework']['total_validators']}")
            logger.info(f"   - Active validators: {manifest['validation_framework']['min_active_validators']}-{manifest['validation_framework']['max_active_validators']}")
            logger.info(f"   - Layers: {len(manifest['validation_framework']['layers'])}")
            return True
        else:
            logger.error("❌ Failed to inject manifest into RAG system")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error injecting manifest: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔍 Injecting StillMe Structural Manifest into RAG...")
    
    # First, ensure manifest exists
    manifest_path = project_root / "data" / "stillme_manifest.json"
    if not manifest_path.exists():
        print("⚠️  Manifest not found. Generating it first...")
        from scripts.generate_manifest import main as generate_main
        if generate_main() != 0:
            print("❌ Failed to generate manifest")
            return 1
    
    # Inject manifest
    success = inject_manifest_to_rag()
    
    if success:
        print("\n✅ SUCCESS: Manifest injected into RAG system!")
        print("\n📋 Next steps:")
        print("   1. StillMe will now retrieve this manifest when answering about validation chain")
        print("   2. StillMe will know it has exactly 19 validators (not 15)")
        print("   3. StillMe will understand the 7-layer architecture")
        print("   4. Regenerate manifest whenever validators change: python scripts/generate_manifest.py")
        return 0
    else:
        print("\n❌ FAILED: Could not inject manifest")
        return 1


if __name__ == "__main__":
    sys.exit(main())

