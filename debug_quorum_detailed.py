#!/usr/bin/env python3
"""Debug quorum window expiry in detail"""
import time
from stillme_core.middleware.habit_store import HabitStore

config = {
    "privacy": {"habits_opt_in": True},
    "quorum": {"threshold": 2, "window_days": 0.001}  # Very short window
}
store = HabitStore(config)

print(f"Quorum threshold: {store.quorum_threshold}")
print(f"Quorum window days: {store.quorum_window_days}")

# First observation
print("\n=== First observation ===")
result1 = store.observe_cue("test cue", "test action", 0.8)
print(f"Result: {result1}")
print(f"Habits: {len(store.habits)}")
print(f"Observations: {store.observations}")

# Wait for window to expire
print("\n=== Waiting for window to expire ===")
time.sleep(0.002)

# Check quorum status
cue_hash = store._hash_cue("test cue")
print(f"Cue hash: {cue_hash}")
print(f"Observations before second call: {store.observations[cue_hash]}")

# Check quorum calculation
now = time.time()
window_start = now - (store.quorum_window_days * 24 * 3600)
print(f"Current time: {now}")
print(f"Window start: {window_start}")
print(f"Window duration: {store.quorum_window_days * 24 * 3600} seconds")

recent_observations = [ts for ts in store.observations[cue_hash] if ts >= window_start]
print(f"Recent observations: {recent_observations}")
print(f"Recent count: {len(recent_observations)}")
print(f"Quorum met: {len(recent_observations) >= store.quorum_threshold}")

# Second observation
print("\n=== Second observation ===")
result2 = store.observe_cue("test cue", "test action", 0.8)
print(f"Result: {result2}")
print(f"Habits: {len(store.habits)}")
print(f"Observations: {store.observations}")
