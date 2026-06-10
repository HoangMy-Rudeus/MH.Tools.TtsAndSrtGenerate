"""Tests for the audio player seam."""

from src.tui.player import FakePlayer


def test_fake_player_records_play_and_stop():
    p = FakePlayer()
    p.play("output/a.mp3")
    p.play("output/b.mp3")
    p.stop()
    assert p.played == ["output/a.mp3", "output/b.mp3"]
    assert p.stop_count == 1
