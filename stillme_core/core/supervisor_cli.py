"""
CLI for Daily Supervisor
"""

import argparse
import sys
from pathlib import Path

# Add the parent directory to the sys.path to allow importing stillme_core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stillme_core.supervisor import get_supervisor


def main():
    parser = argparse.ArgumentParser(description="Daily Supervisor CLI")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run supervisor to collect signals and propose lessons",
    )
    parser.add_argument("--approve", nargs="+", help="Approve lesson proposals by IDs")
    parser.add_argument(
        "--list", action="store_true", help="List current lesson proposals"
    )
    parser.add_argument(
        "--current", action="store_true", help="Show current knowledge pack"
    )

    args = parser.parse_args()

    if not any([args.run, args.approve, args.list, args.current]):
        parser.print_help()
        return

    try:
        supervisor = get_supervisor()

        if args.run:
            print("🔍 Running Daily Supervisor...")
            signals = supervisor.collect_signals()
            proposals = supervisor.propose_lessons(signals)
            proposals_file = supervisor.save_lesson_proposals(proposals)

            print(f"✅ Collected {len(signals.get('agentdev_logs', []))} signals")
            print(f"📝 Generated {len(proposals)} lesson proposals")
            print(f"💾 Saved to: {proposals_file}")

            for proposal in proposals:
                print(f"  - {proposal.id}: {proposal.title}")

        elif args.approve:
            print(f"✅ Approving lesson proposals: {args.approve}")
            knowledge_pack = supervisor.approve_lessons(args.approve)
            print(f"📦 Created knowledge pack: {knowledge_pack.id}")
            print(f"📚 Contains {len(knowledge_pack.lessons)} lessons")
            print(f"📄 Summary: {knowledge_pack.summary}")

        elif args.list:
            print("📋 Current lesson proposals:")
            proposals = supervisor.get_current_proposals()
            if not proposals:
                print("  No proposals found for today")
            else:
                for proposal in proposals:
                    print(f"  - {proposal.id}: {proposal.title}")
                    print(f"    Source: {proposal.source}")
                    print(f"    Created: {proposal.created_at}")
                    print()

        elif args.current:
            print("📦 Current knowledge pack:")
            knowledge_pack = supervisor.get_latest_knowledge_pack()
            if knowledge_pack is None:
                print("  No knowledge pack found")
            else:
                print(f"  ID: {knowledge_pack.id}")
                print(f"  Version: {knowledge_pack.version}")
                print(f"  Created: {knowledge_pack.created_at}")
                print(f"  Lessons: {len(knowledge_pack.lessons)}")
                print(f"  Summary: {knowledge_pack.summary}")
                print()
                for lesson in knowledge_pack.lessons:
                    print(f"    - {lesson.id}: {lesson.title}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
