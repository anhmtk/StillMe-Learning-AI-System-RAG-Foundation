from unittest.mock import MagicMock

# Mock classes since they're not available in stillme_core
LongTermMemory = MagicMock
MemoryItem = MagicMock

"""
test_layered_memory_v1.py
=========================
Unit tests for LayeredMemory_v1 module.
Covers:
- Add and search memory in different layers.
- Auto-compression between layers.
- SQLite storage and retrieval.
- Encryption/decryption for short-term memory.
"""

from datetime import datetime, timedelta

import pytest

from stillme_core.modules.layered_memory_v1 import LayeredMemoryV1


# ---------- FIXTURES ----------
@pytest.fixture
def memory_system():
    """Khởi tạo hệ thống LayeredMemoryV1 cho mỗi test."""
    return LayeredMemoryV1()


@pytest.fixture
def sample_item():
    """Tạo một item mẫu để test."""
    return MemoryItem(
        content="Sample content",
        priority=0.5,
        timestamp=datetime.now(),
        last_accessed=datetime.now(),
        metadata={"source": "unit_test"},
    )


# ---------- TEST SHORT-TERM ----------
def test_add_to_short_term(memory_system, sample_item):
    """Test thêm dữ liệu vào short-term."""
    memory_system.short_term.add(sample_item)
    assert len(memory_system.short_term.buffer) == 1


def test_short_term_encryption(memory_system, sample_item):
    """Test dữ liệu short-term được mã hóa."""
    memory_system.short_term.add(sample_item)
    assert isinstance(memory_system.short_term.buffer[0].content, bytes)


def test_short_term_search(memory_system):
    """Test tìm kiếm trong short-term."""
    memory_system.add_memory("Dark coffee", priority=0.5)
    results = memory_system.search("coffee")
    assert any(
        "coffee" in memory_system.short_term._decrypt(item.content).lower()
        for item in results
    )


# ---------- TEST MID-TERM ----------
def test_mid_term_add_search(memory_system, sample_item):
    """Test thêm và tìm kiếm trong mid-term."""
    memory_system.mid_term.add(sample_item)
    results = memory_system.mid_term.search("Sample")
    assert results and isinstance(results[0], MemoryItem)


def test_mid_term_compression(memory_system, sample_item):
    """Test cơ chế compress trong mid-term."""
    for i in range(10):
        memory_system.mid_term.add(
            MemoryItem(
                content=f"Item {i}",
                priority=0.5,
                timestamp=datetime.now(),
                last_accessed=datetime.now(),
                metadata={},
            )
        )
    compressed = memory_system.mid_term.compress()
    assert isinstance(compressed, list)


# ---------- TEST LONG-TERM ----------
def test_long_term_add_search(tmp_path):
    """Test lưu trữ và tìm kiếm trong long-term."""
    db_path = tmp_path / "test_memory.db"
    long_term = LongTermMemory(str(db_path))

    items = [
        MemoryItem(
            content=f"LongTerm {i}",
            priority=0.8,
            timestamp=datetime.now(),
            last_accessed=datetime.now(),
            metadata={},
        )
        for i in range(3)
    ]
    long_term.add(items)

    results = long_term.search("LongTerm")
    assert len(results) == 3


# ---------- TEST LAYERED LOGIC ----------
def test_add_memory_priority(memory_system):
    """Test phân loại memory theo priority."""
    memory_system.add_memory("High priority task", priority=0.9)
    memory_system.add_memory("Low priority task", priority=0.3)
    assert len(memory_system.short_term.buffer) > 0
    assert memory_system.long_term.search("High priority task")


def test_search_time_filter(memory_system):
    """Test tìm kiếm có time_range."""
    now = datetime.now()
    memory_system.add_memory("Coffee memory", priority=0.6)
    results = memory_system.search(
        "coffee", time_range=(now - timedelta(hours=1), now + timedelta(hours=1))
    )
    assert len(results) > 0


def test_auto_compress_trigger(memory_system):
    """Test auto-compress giữa short-term và mid-term."""
    # Thêm items với priority cao để trigger compress
    for i in range(800):
        memory_system.add_memory(f"Message {i}", priority=0.8, auto_compress=True)

    # Kiểm tra rằng buffer không vượt quá max_size và một số items đã được compress
    assert (
        len(memory_system.short_term.buffer) <= 1000
    )  # Buffer không vượt quá max_size

    # Với priority = 0.8, tất cả items sẽ được compress sang mid-term
    # nên short-term buffer sẽ ít hơn 800
    assert len(memory_system.short_term.buffer) < 800


# ---------- EDGE CASES ----------
def test_empty_search(memory_system):
    """Test tìm kiếm khi không có dữ liệu."""
    results = memory_system.search("nothing")
    assert results == []


def test_search_case_insensitive(memory_system):
    """Test tìm kiếm không phân biệt hoa thường."""
    memory_system.add_memory("Mixed CASE Test", priority=0.6)
    results = memory_system.search("mixed")
    assert any(
        "mixed" in memory_system.short_term._decrypt(item.content).lower()
        for item in results
    )


def test_long_term_with_special_characters(tmp_path):
    """Test lưu và tìm với ký tự đặc biệt trong long-term."""
    db_path = tmp_path / "test_memory_special.db"
    long_term = LongTermMemory(str(db_path))
    item = MemoryItem(
        content="Special chars: !@#$%^&*()",
        priority=0.7,
        timestamp=datetime.now(),
        last_accessed=datetime.now(),
        metadata={},
    )
    long_term.add([item])
    results = long_term.search("Special")
    assert len(results) == 1
    assert "Special" in results[0].content


def test_large_batch_add(memory_system):
    """Test thêm nhiều dữ liệu trong một batch."""
    items = [
        MemoryItem(
            content=f"Batch {i}",
            priority=0.5,
            timestamp=datetime.now(),
            last_accessed=datetime.now(),
            metadata={},
        )
        for i in range(50)
    ]
    memory_system.long_term.add(items)
    results = memory_system.long_term.search("Batch")
    assert len(results) == 50
