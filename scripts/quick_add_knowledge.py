#!/usr/bin/env python3
"""
StillMe IPC Quick Knowledge Input
Script nhanh để thêm kiến thức từ command line
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from scripts.add_manual_knowledge import ManualKnowledgeInput


def main():
    """Quick knowledge input from command line"""
    parser = argparse.ArgumentParser(description="Quick add knowledge for StillMe IPC")
    parser.add_argument("title", help="Knowledge title")
    parser.add_argument("description", help="Knowledge description")
    parser.add_argument("--priority", choices=["low", "medium", "high", "critical"],
                       default="medium", help="Priority level")
    parser.add_argument("--url", help="Source URL (optional)")

    args = parser.parse_args()

    # Add knowledge
    knowledge_input = ManualKnowledgeInput()
    proposal = knowledge_input.add_knowledge(
        title=args.title,
        description=args.description,
        source_url=args.url,
        priority=args.priority
    )

    if proposal:
        print("✅ Knowledge added successfully!")
        print(f"🆔 Proposal ID: {proposal.id}")
        print("📊 Check dashboard: http://localhost:8506")
    else:
        print("❌ Failed to add knowledge")
        sys.exit(1)

if __name__ == "__main__":
    main()
