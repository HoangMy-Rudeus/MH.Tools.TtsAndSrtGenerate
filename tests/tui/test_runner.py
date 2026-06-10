"""Tests for the generation runner seam."""

from src.tui.runner import FakeRunner


def test_fake_runner_emits_progress_and_returns_result(tmp_path):
    runner = FakeRunner(total_lines=3, duration_ms=4200)
    seen = []

    result = runner.run(
        script_path="topics/a.json",
        output_dir=str(tmp_path),
        config=None,
        on_progress=lambda current, total: seen.append((current, total)),
    )

    assert seen == [(1, 3), (2, 3), (3, 3)]
    assert result.success is True
    assert result.duration_ms == 4200


def test_fake_runner_can_simulate_failure(tmp_path):
    runner = FakeRunner(total_lines=1, fail_with="boom")
    result = runner.run("topics/a.json", str(tmp_path), None, lambda c, t: None)

    assert result.success is False
    assert result.error == "boom"
