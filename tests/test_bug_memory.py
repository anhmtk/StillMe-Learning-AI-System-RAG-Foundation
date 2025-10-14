from stillme_core.bug_memory import BugMemory


def test_bugmemory_fingerprint_and_exists(tmp_path):
    path = tmp_path / "bm.jsonl"
    bm = BugMemory(str(path))
    fp = bm.fingerprint("a.py", 10, "ZeroDivisionError")
    assert not bm.exists(fp)
    bm.append(
        {"fingerprint": fp, "file": "a.py", "line": 10, "message": "ZeroDivisionError"}
    )
    assert bm.exists(fp)