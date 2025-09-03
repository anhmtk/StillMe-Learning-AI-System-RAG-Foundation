from stillme_core.sandbox import prepare_sandbox, run_tests_in_sandbox


def test_prepare_and_run(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def x():\n    return 1\n")
    sb = tmp_path / "sb"
    path = prepare_sandbox(repo, sb)
    assert path.exists()
    ok, out, err = run_tests_in_sandbox(["python", "-c", "print('ok')"], path)
    assert ok

