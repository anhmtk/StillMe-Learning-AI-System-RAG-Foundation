from stillme_core.bug_memory import BugMemory


def test_bugmemory_stats_and_similar(tmp_path):
    path = tmp_path / "bm.jsonl"
    bm = BugMemory(str(path))
    fp = bm.fingerprint("a.py", 10, "ZeroDivisionError")
    bm.append({"fingerprint": fp, "file": "a.py", "line": 10, "message": "ZeroDivisionError"})
    bm.append({"fingerprint": fp, "file": "a.py", "line": 11, "message": "ZeroDivisionError"})
    assert bm.exists(fp)
    sims = bm.find_similar(fp)
    assert len(sims) >= 2
    stats = bm.stats_by_file()
    assert stats.get("a.py", 0) >= 2

