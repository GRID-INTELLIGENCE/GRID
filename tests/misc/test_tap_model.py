import pytest

pytest.importorskip("acoustics.tap_model", reason="acoustics.tap_model module not implemented")

from acoustics.tap_model import Room, Source, modal_frequencies, reflection_times_and_amplitudes


def test_reflection_times_basic():
    r = Room(10.0, 8.0, 3.0)
    s = Source(1.0, 2.0, 0.5)
    refs = reflection_times_and_amplitudes(r, s, tap_energy=1.0)
    # expect 6 entries
    assert len(refs) == 6
    # times should be > 0 and sorted
    times = [t for t, *_ in refs]
    assert all(t > 0.0 for t in times)
    assert times == sorted(times)


def test_modal_frequencies_nonzero():
    r = Room(5.0, 4.0, 3.0)
    modes = modal_frequencies(r, max_mode=2)
    assert any(freq > 0 for (_, freq) in modes)
    # ensure (1,0,0) mode exists
    assert any(mode == (1, 0, 0) for (mode, _) in modes)
