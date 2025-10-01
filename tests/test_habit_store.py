"""
Tests for Habit Store
"""
import time

from stillme_core.middleware.habit_store import HabitEntry, HabitStats, HabitStore


class TestHabitStore:
    """Test HabitStore functionality"""

    def test_habit_store_disabled_by_default(self):
        """Test that habit store is disabled by default (opt-out)"""
        store = HabitStore()
        assert not store.is_enabled()
        assert not store.habits_opt_in

    def test_habit_store_enabled_with_opt_in(self):
        """Test habit store can be enabled with opt-in"""
        config = {
            "privacy": {
                "habits_opt_in": True
            }
        }
        store = HabitStore(config)
        assert store.is_enabled()
        assert store.habits_opt_in

    def test_cue_hashing_privacy(self):
        """Test that cues are hashed for privacy"""
        config = {
            "privacy": {
                "habits_opt_in": True,
                "hash_cues": True
            }
        }
        store = HabitStore(config)

        cue_hash = store._hash_cue("Hello world")
        assert cue_hash != "Hello world"
        assert len(cue_hash) == 16  # First 16 chars of SHA256
        assert cue_hash.isalnum()  # Should be hex

    def test_cue_hashing_disabled(self):
        """Test that cue hashing can be disabled"""
        config = {
            "privacy": {
                "habits_opt_in": True,
                "hash_cues": False
            }
        }
        store = HabitStore(config)

        cue_hash = store._hash_cue("Hello world")
        assert cue_hash == "Hello world"

    def test_quorum_requirement(self):
        """Test that habits require quorum before creation"""
        config = {
            "privacy": {"habits_opt_in": True},
            "quorum": {"threshold": 2, "window_days": 1}
        }
        store = HabitStore(config)

        # First observation - should not create habit
        result = store.observe_cue("test cue", "test action", 0.8)
        assert not result
        assert len(store.habits) == 0

        # Second observation - should create habit (quorum met)
        result = store.observe_cue("test cue", "test action", 0.8)
        assert result
        assert len(store.habits) == 1

    def test_quorum_window_expiry(self):
        """Test that quorum window expires"""
        config = {
            "privacy": {"habits_opt_in": True},
            "quorum": {"threshold": 2, "window_days": 0.00001}  # Very short window (0.86 seconds)
        }
        store = HabitStore(config)

        # First observation
        store.observe_cue("test cue", "test action", 0.8)

        # Wait for window to expire
        time.sleep(1.0)  # Wait 1 second for window to expire

        # Second observation - should not create habit (window expired)
        result = store.observe_cue("test cue", "test action", 0.8)
        assert not result
        assert len(store.habits) == 0

    def test_habit_creation_and_update(self):
        """Test habit creation and updates"""
        config = {"privacy": {"habits_opt_in": True}, "quorum": {"threshold": 1}}
        store = HabitStore(config)

        # Create habit
        result = store.observe_cue("test cue", "test action", 0.8, "user1", "tenant1")
        assert result
        assert len(store.habits) == 1

        habit = list(store.habits.values())[0]
        assert habit.action == "test action"
        assert habit.confidence == 0.8
        assert habit.frequency == 1
        assert habit.metadata["first_user"] == "user1"
        assert habit.metadata["first_tenant"] == "tenant1"

        # Update habit
        result = store.observe_cue("test cue", "updated action", 0.9, "user2", "tenant2")
        assert result
        assert len(store.habits) == 1

        habit = list(store.habits.values())[0]
        assert habit.action == "updated action"  # Action updated
        assert habit.confidence == 0.9  # Higher confidence kept
        assert habit.frequency == 2  # Frequency increased
        assert habit.metadata["last_user"] == "user2"
        assert habit.metadata["last_tenant"] == "tenant2"

    def test_habit_score_calculation(self):
        """Test habit score calculation"""
        config = {"privacy": {"habits_opt_in": True}, "quorum": {"threshold": 1}}
        store = HabitStore(config)

        # Create habit
        store.observe_cue("test cue", "test action", 0.8)

        # Get score
        score, action = store.get_habit_score("test cue")
        assert score > 0
        assert action == "test action"

        # Test non-existent cue
        score, action = store.get_habit_score("non-existent")
        assert score == 0
        assert action is None

    def test_habit_decay(self):
        """Test habit decay over time"""
        config = {
            "privacy": {"habits_opt_in": True},
            "quorum": {"threshold": 1},
            "decay": {"half_life_days": 0.001, "min_threshold": 0.1}  # Very fast decay
        }
        store = HabitStore(config)

        # Create habit
        store.observe_cue("test cue", "test action", 0.8)

        # Get initial score
        score, _ = store.get_habit_score("test cue")
        assert score > 0

        # Wait for decay
        time.sleep(0.002)

        # Score should be lower or habit removed
        score, action = store.get_habit_score("test cue")
        if score > 0:
            assert score < 0.8  # Should be decayed
        else:
            assert action is None  # Habit removed due to decay

    def test_ttl_expiration(self):
        """Test TTL expiration of habits"""
        config = {
            "privacy": {"habits_opt_in": True, "ttl_days": 0.00001},  # Very short TTL (0.86 seconds)
            "quorum": {"threshold": 1}
        }
        store = HabitStore(config)

        # Create habit
        store.observe_cue("test cue", "test action", 0.8)
        assert len(store.habits) == 1

        # Wait for TTL expiration
        time.sleep(1.0)  # Wait 1 second for TTL to expire

        # Trigger cleanup
        store.cleanup_expired()

        # Habit should be removed
        assert len(store.habits) == 0

    def test_export_habits(self):
        """Test habit export functionality"""
        config = {"privacy": {"habits_opt_in": True}, "quorum": {"threshold": 1}}
        store = HabitStore(config)

        # Create habits
        store.observe_cue("cue1", "action1", 0.8, "user1", "tenant1")
        store.observe_cue("cue2", "action2", 0.9, "user2", "tenant2")

        # Export all habits
        export_data = store.export_habits()
        assert "habits" in export_data
        assert "metadata" in export_data
        assert len(export_data["habits"]) == 2
        assert export_data["metadata"]["opt_in"] is True

        # Export user-specific habits
        user_habits = store.export_habits(user_id="user1")
        assert len(user_habits["habits"]) == 1
        assert user_habits["habits"][0]["metadata"]["first_user"] == "user1"

    def test_delete_habits(self):
        """Test habit deletion functionality"""
        config = {"privacy": {"habits_opt_in": True}, "quorum": {"threshold": 1}}
        store = HabitStore(config)

        # Create habits
        store.observe_cue("cue1", "action1", 0.8, "user1", "tenant1")
        store.observe_cue("cue2", "action2", 0.9, "user2", "tenant2")
        assert len(store.habits) == 2

        # Delete user1 habits
        deleted = store.delete_habits(user_id="user1")
        assert deleted == 1
        assert len(store.habits) == 1

        # Delete all habits
        deleted = store.delete_habits()
        assert deleted == 1
        assert len(store.habits) == 0

    def test_habit_poisoning_prevention(self):
        """Test that single user cannot poison habits (quorum requirement)"""
        config = {
            "privacy": {"habits_opt_in": True},
            "quorum": {"threshold": 3, "window_days": 1}
        }
        store = HabitStore(config)

        # Single user tries to create habit with multiple observations
        for i in range(2):  # Below quorum threshold
            result = store.observe_cue("poison cue", "bad action", 0.8, "attacker", "tenant1")
            assert not result

        assert len(store.habits) == 0

        # Multiple users create legitimate habit
        store.observe_cue("legitimate cue", "good action", 0.8, "user1", "tenant1")
        store.observe_cue("legitimate cue", "good action", 0.8, "user2", "tenant1")
        result = store.observe_cue("legitimate cue", "good action", 0.8, "user3", "tenant1")
        assert result
        assert len(store.habits) == 1

    def test_statistics_tracking(self):
        """Test statistics tracking"""
        config = {"privacy": {"habits_opt_in": True}, "quorum": {"threshold": 1}}
        store = HabitStore(config)

        # Initial stats
        stats = store.get_stats()
        assert stats["total_habits"] == 0
        assert stats["active_habits"] == 0

        # Create habits
        store.observe_cue("cue1", "action1", 0.8)
        store.observe_cue("cue2", "action2", 0.9)

        # Check updated stats
        stats = store.get_stats()
        assert stats["total_habits"] == 2
        assert stats["active_habits"] == 2
        assert stats["total_observations"] >= 2
        assert stats["avg_confidence"] > 0

    def test_reset_functionality(self):
        """Test reset functionality"""
        config = {"privacy": {"habits_opt_in": True}, "quorum": {"threshold": 1}}
        store = HabitStore(config)

        # Create habits
        store.observe_cue("cue1", "action1", 0.8)
        assert len(store.habits) > 0

        # Reset
        store.reset()
        assert len(store.habits) == 0
        assert len(store.observations) == 0

class TestHabitEntry:
    """Test HabitEntry dataclass"""

    def test_habit_entry_creation(self):
        """Test HabitEntry creation"""
        entry = HabitEntry(
            cue_hash="test_hash",
            action="test_action",
            confidence=0.8,
            frequency=5,
            first_seen=time.time(),
            last_seen=time.time()
        )

        assert entry.cue_hash == "test_hash"
        assert entry.action == "test_action"
        assert entry.confidence == 0.8
        assert entry.frequency == 5
        assert entry.decay_factor == 1.0
        assert entry.metadata == {}

    def test_habit_entry_metadata(self):
        """Test HabitEntry with metadata"""
        metadata = {"user": "test_user", "tenant": "test_tenant"}
        entry = HabitEntry(
            cue_hash="test_hash",
            action="test_action",
            confidence=0.8,
            frequency=1,
            first_seen=time.time(),
            last_seen=time.time(),
            metadata=metadata
        )

        assert entry.metadata == metadata

class TestHabitStats:
    """Test HabitStats dataclass"""

    def test_habit_stats_defaults(self):
        """Test HabitStats default values"""
        stats = HabitStats()

        assert stats.total_habits == 0
        assert stats.active_habits == 0
        assert stats.total_observations == 0
        assert stats.avg_confidence == 0.0
        assert stats.oldest_habit_days == 0.0
        assert stats.newest_habit_days == 0.0
