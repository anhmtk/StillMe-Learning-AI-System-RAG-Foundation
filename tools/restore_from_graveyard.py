#!/usr/bin/env python3
"""
🔄 Restore From Graveyard Tool
Restore files từ graveyard về vị trí cũ
"""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from quarantine_move import QuarantineMover


def main():
    """Main function để restore files"""
    print("🔄 Restore From Graveyard Tool")
    print("=" * 50)

    mover = QuarantineMover()

    # List current quarantined files
    print("📋 Current quarantined files:")
    mover.list_quarantined_files()

    print("\n" + "=" * 50)

    # Restore files
    mover.restore_from_graveyard()

if __name__ == "__main__":
    main()
