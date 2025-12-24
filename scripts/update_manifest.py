#!/usr/bin/env python3
"""
Update StillMe Manifest - Generate and Inject in One Command

This script:
1. Generates the manifest from current codebase
2. Injects it into RAG system
3. Increments knowledge version (invalidates cache)

Usage:
    python scripts/update_manifest.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from scripts.generate_manifest import main as generate_main
from scripts.inject_manifest_to_rag import inject_manifest_to_rag


def main():
    """Main function to update manifest"""
    print("🔄 Updating StillMe Structural Manifest...")
    print("=" * 60)
    
    # Step 1: Generate manifest
    print("\n📝 Step 1: Generating manifest from codebase...")
    generate_result = generate_main()
    if generate_result != 0:
        print("❌ Failed to generate manifest")
        return 1
    
    # Step 2: Inject to RAG
    print("\n💾 Step 2: Injecting manifest into RAG system...")
    inject_result = inject_manifest_to_rag()
    if not inject_result:
        print("❌ Failed to inject manifest into RAG")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS: Manifest updated and injected!")
    print("\n📋 Summary:")
    print("   - Manifest generated from current codebase")
    print("   - Manifest injected into ChromaDB with CRITICAL_FOUNDATION priority")
    print("   - Knowledge version incremented (cache invalidated)")
    print("\n💡 Next time StillMe is asked about validators, it will use the updated manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())

