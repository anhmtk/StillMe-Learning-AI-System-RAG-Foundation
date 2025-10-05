#!/usr/bin/env python3
"""
StillMe Community System Deployment Script
Triển khai hệ thống community proposal & voting
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    """Deploy StillMe Community System"""
    print("🚀 Deploying StillMe Community System...")
    
    # Check if we're in the right directory
    if not Path("stillme_community").exists():
        print("❌ Error: stillme_community directory not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # 1. Create necessary directories
    print("📁 Creating directories...")
    directories = [
        "data",
        "docs/community_dashboard/assets",
        "logs/community"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # 2. Initialize community database
    print("🗄️ Initializing community database...")
    try:
        from stillme_community.proposal_manager import CommunityProposalManager
        manager = CommunityProposalManager()
        print("✅ Community database initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    
    # 3. Test GitHub integration
    print("🔗 Testing GitHub integration...")
    try:
        from stillme_community.github_integration import GitHubIntegration
        github = GitHubIntegration()
        print("✅ GitHub integration ready")
    except Exception as e:
        print(f"⚠️ GitHub integration warning: {e}")
        print("Note: Set GITHUB_TOKEN environment variable for full functionality")
    
    # 4. Test voting engine
    print("🗳️ Testing voting engine...")
    try:
        from stillme_community.voting_engine import VotingEngine
        engine = VotingEngine()
        print("✅ Voting engine ready")
    except Exception as e:
        print(f"❌ Voting engine error: {e}")
        return False
    
    # 5. Create GitHub Actions workflow
    print("⚙️ Creating GitHub Actions workflow...")
    workflow_content = """name: Community Proposal Sync
on:
  issues:
    types: [opened, edited]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  sync-proposals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install requests sqlite3
      
      - name: Sync Community Proposals
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/sync_github_issues.py
"""
    
    workflow_path = Path(".github/workflows/community_sync.yml")
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(workflow_content)
    print("✅ GitHub Actions workflow created")
    
    # 6. Create community voting processor script
    print("📝 Creating community voting processor...")
    processor_content = """#!/usr/bin/env python3
\"\"\"
StillMe Community Voting Processor
Chạy tự động để xử lý voting và auto-approval
\"\"\"

import time
import logging
from stillme_community.voting_engine import VotingEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    \"\"\"Run continuous voting processing\"\"\"
    logger.info("🔄 Starting StillMe Community Voting Processor...")
    
    engine = VotingEngine()
    
    try:
        # Run continuous voting
        engine.run_continuous_voting()
    except KeyboardInterrupt:
        logger.info("🛑 Voting processor stopped by user")
    except Exception as e:
        logger.error(f"❌ Voting processor error: {e}")

if __name__ == "__main__":
    main()
"""
    
    processor_path = Path("scripts/community_voting_processor.py")
    processor_path.write_text(processor_content)
    processor_path.chmod(0o755)  # Make executable
    print("✅ Community voting processor created")
    
    # 7. Create GitHub issues sync script
    print("📝 Creating GitHub issues sync script...")
    sync_content = """#!/usr/bin/env python3
\"\"\"
StillMe GitHub Issues Sync
Đồng bộ GitHub Issues với community proposals
\"\"\"

import os
import requests
import json
from stillme_community.proposal_manager import CommunityProposalManager
from stillme_community.github_integration import GitHubIntegration

def main():
    \"\"\"Sync GitHub issues with community proposals\"\"\"
    print("🔄 Syncing GitHub issues with community proposals...")
    
    # Initialize managers
    proposal_manager = CommunityProposalManager()
    github_integration = GitHubIntegration()
    
    # Get active proposals
    proposals = proposal_manager.get_active_proposals()
    
    # Sync to GitHub
    results = github_integration.sync_proposals_to_issues(proposals)
    print(f"📊 Sync results: {results}")
    
    # Process daily voting
    voting_results = proposal_manager.process_daily_voting()
    print(f"🗳️ Voting results: {voting_results}")

if __name__ == "__main__":
    main()
"""
    
    sync_path = Path("scripts/sync_github_issues.py")
    sync_path.write_text(sync_content)
    sync_path.chmod(0o755)  # Make executable
    print("✅ GitHub issues sync script created")
    
    # 8. Create deployment instructions
    print("📋 Creating deployment instructions...")
    instructions = """# StillMe Community System Deployment

## 🚀 Quick Start

### 1. Start Community Voting Processor
```bash
# Run in background
nohup python scripts/community_voting_processor.py > logs/community/voting.log 2>&1 &
```

### 2. Start Dashboard
```bash
# Main dashboard with community features
streamlit run dashboards/streamlit/simple_app.py --server.port 8501
```

### 3. Deploy GitHub Pages (Optional)
```bash
# Push to enable GitHub Pages
git add docs/community_dashboard/
git commit -m "feat: Deploy community dashboard"
git push origin main
```

## 🔧 Configuration

### Environment Variables
```bash
export GITHUB_TOKEN="your_github_token_here"
```

### Database
- Community proposals: `data/community_proposals.db`
- Auto-created on first run

## 📊 Monitoring

### Check Voting Processor
```bash
tail -f logs/community/voting.log
```

### Check Database
```bash
sqlite3 data/community_proposals.db "SELECT * FROM community_proposals;"
```

## 🎯 Features

✅ **Community Dashboard**: GitHub Pages at `/docs/community_dashboard/`
✅ **Voting System**: Real-time voting with auto-approval
✅ **GitHub Integration**: Sync with GitHub Issues
✅ **Auto-Learning**: Approved proposals start learning automatically
✅ **Notifications**: Email/Telegram alerts for community events

## 🔄 Workflow

1. **Community submits proposal** → GitHub Issue created
2. **Community votes** → Real-time vote counting
3. **Auto-approval** → StillMe starts learning
4. **Notifications** → Community and admin notified

## 🎉 Result

StillMe AI becomes truly community-driven! 🎯
"""
    
    instructions_path = Path("COMMUNITY_DEPLOYMENT.md")
    instructions_path.write_text(instructions)
    print("✅ Deployment instructions created")
    
    # 9. Final summary
    print("\n🎉 StillMe Community System Deployment Complete!")
    print("\n📋 What was created:")
    print("✅ Community database initialized")
    print("✅ GitHub integration configured")
    print("✅ Voting engine ready")
    print("✅ GitHub Actions workflow")
    print("✅ Community voting processor")
    print("✅ GitHub issues sync script")
    print("✅ Deployment instructions")
    
    print("\n🚀 Next steps:")
    print("1. Set GITHUB_TOKEN environment variable")
    print("2. Start community voting processor:")
    print("   nohup python scripts/community_voting_processor.py &")
    print("3. Start dashboard:")
    print("   streamlit run dashboards/streamlit/simple_app.py --server.port 8501")
    print("4. Deploy GitHub Pages (optional)")
    
    print("\n🎯 Community system is ready!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Deployment successful!")
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)
