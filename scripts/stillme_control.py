#!/usr/bin/env python3
"""
StillMe IPC Master Control
Script điều khiển chính cho tất cả chức năng của StillMe
"""

import sys
import argparse
import subprocess
from pathlib import Path

def main():
    """Master control for StillMe IPC"""
    parser = argparse.ArgumentParser(description="StillMe IPC Master Control")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start real learning system
    start_parser = subparsers.add_parser("start", help="Start real learning system")
    
    # Start background service
    background_parser = subparsers.add_parser("background", help="Start background service (auto-discovery)")
    
    # Discover knowledge
    discover_parser = subparsers.add_parser("discover", help="Discover new knowledge")
    
    # Add manual knowledge
    add_parser = subparsers.add_parser("add", help="Add manual knowledge")
    add_parser.add_argument("title", help="Knowledge title")
    add_parser.add_argument("description", help="Knowledge description")
    add_parser.add_argument("--priority", choices=["low", "medium", "high", "critical"], 
                           default="medium", help="Priority level")
    add_parser.add_argument("--url", help="Source URL (optional)")
    
    # Quick add knowledge
    quick_parser = subparsers.add_parser("quick", help="Quick add knowledge")
    quick_parser.add_argument("title", help="Knowledge title")
    quick_parser.add_argument("description", help="Knowledge description")
    quick_parser.add_argument("--priority", choices=["low", "medium", "high", "critical"], 
                             default="medium", help="Priority level")
    quick_parser.add_argument("--url", help="Source URL (optional)")
    
    # Start automation
    auto_parser = subparsers.add_parser("automation", help="Start smart automation")
    
    # Launch dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch dashboard")
    dashboard_parser.add_argument("--port", type=int, default=8506, help="Dashboard port")
    
    # Setup notifications
    notify_parser = subparsers.add_parser("setup-notifications", help="Setup email and Telegram notifications")
    
    # Windows Service management
    service_parser = subparsers.add_parser("service", help="Manage Windows Service")
    service_parser.add_argument("action", choices=["install", "uninstall", "start", "stop", "restart", "status"],
                               help="Service action")
    
    # Founder knowledge input
    founder_parser = subparsers.add_parser("founder", help="Add founder knowledge (auto-approved)")
    founder_parser.add_argument("title", help="Knowledge title")
    founder_parser.add_argument("description", help="Knowledge description")
    founder_parser.add_argument("--priority", choices=["low", "medium", "high", "critical"], 
                                default="high", help="Priority level")
    founder_parser.add_argument("--url", help="Source URL (optional)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == "start":
        print("🚀 Starting StillMe IPC Real Learning System...")
        subprocess.run([sys.executable, "scripts/start_real_learning.py"])
        
    elif args.command == "background":
        print("🔄 Starting StillMe IPC Background Service...")
        subprocess.run([sys.executable, "scripts/stillme_background_service.py"])
        
    elif args.command == "discover":
        print("🔍 Discovering new knowledge...")
        subprocess.run([sys.executable, "scripts/knowledge_discovery.py"])
        
    elif args.command == "add":
        print("📚 Adding manual knowledge...")
        subprocess.run([
            sys.executable, "scripts/add_manual_knowledge.py",
            "--title", args.title,
            "--description", args.description,
            "--priority", args.priority
        ] + (["--url", args.url] if args.url else []))
        
    elif args.command == "quick":
        print("⚡ Quick adding knowledge...")
        subprocess.run([
            sys.executable, "scripts/quick_add_knowledge.py",
            args.title,
            args.description,
            "--priority", args.priority
        ] + (["--url", args.url] if args.url else []))
        
    elif args.command == "automation":
        print("🤖 Starting smart automation...")
        subprocess.run([sys.executable, "scripts/smart_automation.py"])
        
    elif args.command == "dashboard":
        print(f"📊 Launching dashboard on port {args.port}...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboards/streamlit/simple_app.py",
            "--server.port", str(args.port),
            "--browser.gatherUsageStats", "false"
        ])
        
    elif args.command == "founder":
        print("👑 Adding founder knowledge (auto-approved)...")
        subprocess.run([
            sys.executable, "scripts/founder_knowledge_input.py",
            "--title", args.title,
            "--description", args.description,
            "--priority", args.priority
        ] + (["--url", args.url] if args.url else []))
        
    elif args.command == "setup-notifications":
        print("📧📱 Setting up notifications...")
        subprocess.run([sys.executable, "scripts/setup_notifications.py"])
        
    elif args.command == "service":
        print(f"🪟 Managing Windows Service: {args.action}")
        subprocess.run([sys.executable, "scripts/install_windows_service.py", args.action])

if __name__ == "__main__":
    main()
