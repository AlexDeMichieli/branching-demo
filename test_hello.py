"""Tests that gate CI on both branches.

Passing this test proves refresh_token actually rotates the value. Failing
means the token isn't being refreshed (the demo bug).
"""
from hello import refresh_token


def test_refresh_token_actually_rotates_the_value():
    token = refresh_token({"token": "abc"})
    assert token is not None
    assert token != "abc", (
        "refresh_token returned the input token unchanged. "
        "A refresh must produce a different value."
    )


def test_refresh_token_returns_none_for_missing_user():
    assert refresh_token(None) is None
    assert refresh_token({}) is None
