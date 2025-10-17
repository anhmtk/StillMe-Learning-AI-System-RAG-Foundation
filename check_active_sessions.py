#!/usr/bin/env python3
"""
Check Active Sessions
"""

from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem

def check_sessions():
    learning_system = EvolutionaryLearningSystem()
    sessions = learning_system.get_active_sessions()
    print(f'Active sessions: {len(sessions)}')
    for session_id, data in sessions.items():
        print(f'Session: {session_id[:8]}... - {data.get("title", "Unknown")} - Status: {data.get("status", "Unknown")}')
        print(f'  Progress: {data.get("progress", 0)}%')
        print(f'  Started: {data.get("started_at", "Unknown")}')

if __name__ == "__main__":
    check_sessions()
