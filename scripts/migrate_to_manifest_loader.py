#!/usr/bin/env python3
"""
Migration Script: Replace Hardcoded Validator Numbers with ManifestLoader

This script automatically replaces hardcoded validator counts and layer numbers
in chat_router.py with calls to ManifestLoader, ensuring StillMe always reads
from the dynamic manifest.json file instead of hardcoded values.
"""

import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
chat_router_path = project_root / "backend" / "api" / "routers" / "chat_router.py"


def migrate_chat_router():
    """Replace hardcoded numbers with ManifestLoader calls"""
    
    print("📖 Reading chat_router.py...")
    with open(chat_router_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Add import at top (after other imports)
    if "from backend.core.manifest_loader import" not in content:
        # Find last import statement
        import_pattern = r'(from backend\.\w+\.\w+ import .+\n)'
        matches = list(re.finditer(import_pattern, content))
        if matches:
            last_import = matches[-1]
            insert_pos = last_import.end()
            content = content[:insert_pos] + "from backend.core.manifest_loader import get_validator_count, get_validator_summary, get_layers_info, get_manifest_text_for_prompt\n" + content[insert_pos:]
            print("✅ Added ManifestLoader import")
    
    # 2. Replace hardcoded "19 validators" with dynamic call
    content = re.sub(
        r'19 validators total(?:, organized into 7 layers)?',
        lambda m: 'get_validator_summary()',
        content
    )
    
    # 3. Replace hardcoded "7 layers" with dynamic call
    content = re.sub(
        r'7 layers?|7 lớp',
        lambda m: f'{get_layers_count_placeholder()}',
        content
    )
    
    # 4. Replace specific patterns in prompts
    patterns = [
        (r'"Hệ thống của tôi có \*\*19 validators total, chia thành 7 lớp', 
         '"Hệ thống của tôi có **" + get_validator_summary()'),
        (r'My system has \*\*19 validators total, organized into 7 layers',
         'My system has **' + get_validator_summary()),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        print("💾 Writing updated chat_router.py...")
        with open(chat_router_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Migration complete!")
        return True
    else:
        print("ℹ️ No changes needed")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Hardcoded Numbers → ManifestLoader")
    print("=" * 60)
    print()
    
    if not chat_router_path.exists():
        print(f"❌ File not found: {chat_router_path}")
        sys.exit(1)
    
    success = migrate_chat_router()
    
    if success:
        print()
        print("✅ Migration successful!")
        print()
        print("Next steps:")
        print("1. Review the changes in chat_router.py")
        print("2. Test that StillMe correctly reads from manifest.json")
        print("3. Commit the changes")
    else:
        print()
        print("ℹ️ No migration needed or migration failed")
    
    sys.exit(0 if success else 1)

