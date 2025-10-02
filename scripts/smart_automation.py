#!/usr/bin/env python3
"""
StillMe IPC Smart Automation
===========================

Automation system với kiểm soát thông minh và giới hạn tần suất.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


class SmartAutomation:
    """Smart automation system với kiểm soát"""

    def __init__(self):
        self.status_file = project_root / "artifacts" / "automation_status.json"
        self.config_file = project_root / "data" / "config" / "automation_config.json"
        self.load_config()

    def load_config(self):
        """Load automation configuration"""
        default_config = {
            "automation_enabled": True,  # Default to True
            "enabled": True,  # For backward compatibility
            "max_proposals_per_hour": 2,  # Giới hạn 2 proposals/giờ
            "max_proposals_per_day": 10,  # Giới hạn 10 proposals/ngày
            "proposal_interval_minutes": 30,  # Tạo proposal mỗi 30 phút
            "last_proposal_time": None,
            "proposals_created_today": 0,
            "proposals_created_this_hour": 0,
            "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.config = json.load(f)
                # Reset daily counters if new day
                if self.config.get("last_reset_date") != datetime.now().strftime(
                    "%Y-%m-%d"
                ):
                    self.config["proposals_created_today"] = 0
                    self.config["last_reset_date"] = datetime.now().strftime("%Y-%m-%d")
            except:
                self.config = default_config
        else:
            self.config = default_config

        # Also check dashboard session state
        try:
            session_file = project_root / "artifacts" / "dashboard_session.json"
            if session_file.exists():
                with open(session_file) as f:
                    session_data = json.load(f)
                    if "automation_enabled" in session_data:
                        self.config["enabled"] = session_data["automation_enabled"]
        except:
            pass

        self.save_config()

    def save_config(self):
        """Save automation configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def can_create_proposal(self) -> bool:
        """Check if we can create a new proposal"""
        if not self.config.get("enabled", False) and not self.config.get(
            "automation_enabled", False
        ):
            return False

        now = datetime.now()
        last_proposal_time = self.config.get("last_proposal_time")

        # Check hourly limit
        if self.config.get("proposals_created_this_hour", 0) >= self.config.get(
            "max_proposals_per_hour", 2
        ):
            return False

        # Check daily limit
        if self.config.get("proposals_created_today", 0) >= self.config.get(
            "max_proposals_per_day", 10
        ):
            return False

        # Check interval
        if last_proposal_time:
            last_time = datetime.fromisoformat(last_proposal_time)
            interval_minutes = self.config.get("proposal_interval_minutes", 30)
            if (now - last_time).total_seconds() < interval_minutes * 60:
                return False

        return True

    def create_proposal(self):
        """Create a new learning proposal"""
        if not self.can_create_proposal():
            return None

        try:
            from stillme_core.learning.proposals_manager import ProposalsManager

            manager = ProposalsManager()

            # Create proposal data
            proposal_data = {
                "title": "Data Science with Python",
                "description": "Learn data science fundamentals including data analysis, visualization, and machine learning with Python",
                "learning_objectives": [
                    "Master data analysis with pandas",
                    "Create visualizations with matplotlib and seaborn",
                    "Apply statistical analysis methods",
                    "Build predictive models",
                ],
                "prerequisites": [
                    "Basic Python knowledge",
                    "Understanding of statistics",
                    "Familiarity with data analysis",
                ],
                "expected_outcomes": [
                    "Analyze complex datasets",
                    "Create publication-ready visualizations",
                    "Build machine learning models",
                    "Apply data science to real problems",
                ],
                "estimated_duration": 240,  # 4 hours
                "quality_score": 0.92,
                "source": "ai_generated",
                "priority": "high",
                "risk_assessment": {
                    "complexity": "medium",
                    "time_commitment": "high",
                    "prerequisites": "medium",
                    "practical_value": "very_high",
                },
            }

            proposal = manager.create_proposal(**proposal_data)

            # Update counters
            now = datetime.now()
            self.config["last_proposal_time"] = now.isoformat()
            self.config["proposals_created_today"] = (
                self.config.get("proposals_created_today", 0) + 1
            )
            self.config["proposals_created_this_hour"] = (
                self.config.get("proposals_created_this_hour", 0) + 1
            )
            self.save_config()

            print(f"✅ Created proposal: {proposal.title}")
            return proposal

        except Exception as e:
            print(f"❌ Failed to create proposal: {e}")
            return None

    def reset_hourly_counter(self):
        """Reset hourly counter"""
        now = datetime.now()
        if now.minute == 0:  # Reset at the top of each hour
            self.config["proposals_created_this_hour"] = 0
            self.save_config()

    def get_status(self):
        """Get automation status"""
        return {
            "enabled": self.config.get("enabled", False),
            "proposals_created_today": self.config.get("proposals_created_today", 0),
            "proposals_created_this_hour": self.config.get(
                "proposals_created_this_hour", 0
            ),
            "max_per_day": self.config.get("max_proposals_per_day", 10),
            "max_per_hour": self.config.get("max_proposals_per_hour", 2),
            "next_proposal_in": self.get_next_proposal_time(),
        }

    def get_next_proposal_time(self):
        """Get time until next proposal can be created"""
        if not self.config.get("enabled", False):
            return "Automation disabled"

        last_proposal_time = self.config.get("last_proposal_time")
        if not last_proposal_time:
            return "Ready to create"

        last_time = datetime.fromisoformat(last_proposal_time)
        interval_minutes = self.config.get("proposal_interval_minutes", 30)
        next_time = last_time + timedelta(minutes=interval_minutes)
        now = datetime.now()

        if next_time <= now:
            return "Ready to create"
        else:
            diff = next_time - now
            return f"{diff.seconds // 60} minutes"


def main():
    """Main function"""
    print("🧠 StillMe IPC Smart Automation")
    print("=" * 40)

    automation = SmartAutomation()

    # Check if automation is enabled
    if not automation.config.get("enabled", False) and not automation.config.get(
        "automation_enabled", False
    ):
        print("🔴 Automation is disabled.")
        print(
            "Enable it in the dashboard sidebar to start automatic proposal creation."
        )
        return

    print("🟢 Automation is enabled!")

    # Show status
    status = automation.get_status()
    print("\n📊 Status:")
    print(
        f"• Proposals created today: {status['proposals_created_today']}/{status['max_per_day']}"
    )
    print(
        f"• Proposals created this hour: {status['proposals_created_this_hour']}/{status['max_per_hour']}"
    )
    print(f"• Next proposal: {status['next_proposal_in']}")

    # Try to create proposal
    if automation.can_create_proposal():
        proposal = automation.create_proposal()
        if proposal:
            print("\n🎉 Proposal created successfully!")
            print(f"📋 Title: {proposal.title}")
            print(f"📊 Quality Score: {proposal.quality_score}")
        else:
            print("\n❌ Failed to create proposal.")
    else:
        print("\n⏳ Cannot create proposal right now.")
        print(f"Next proposal: {status['next_proposal_in']}")


if __name__ == "__main__":
    main()
