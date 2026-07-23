import pytest

from pyenzyme.composer import _fetch_with_fetchers


def test_returns_first_successful_fetcher():
    def boom(_):
        raise ConnectionError("down")

    def ok(entity_id):
        return f"fetched:{entity_id}"

    assert _fetch_with_fetchers("X1", [boom, ok], "protein") == "fetched:X1"


def test_error_aggregates_every_fetcher_reason():
    def bad_request(_):
        raise ValueError("400 Bad Request")

    def not_found(_):
        raise KeyError("404")

    with pytest.raises(ValueError) as exc:
        _fetch_with_fetchers("X1", [bad_request, not_found], "protein")

    msg = str(exc.value)
    # names the entity, the type, and each fetcher's real failure reason
    assert "No protein fetcher succeeded for X1" in msg
    assert "bad_request: ValueError: 400 Bad Request" in msg
    assert "not_found: KeyError" in msg
