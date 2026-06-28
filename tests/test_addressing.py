import pytest

from a2a_protocol_core.addressing import assert_valid_pay_uri, is_valid_pay_uri


@pytest.mark.parametrize(
    "uri",
    [
        "pay:alice",
        "pay:vendor.alpha",
        "pay:agent.compute.us-east",
        "pay:a",
        "pay:a1-b2.c3",
    ],
)
def test_valid_uris(uri):
    assert is_valid_pay_uri(uri)
    assert assert_valid_pay_uri(uri) == uri


@pytest.mark.parametrize(
    "uri",
    [
        "",
        "alice",            # missing scheme
        "pay:",             # empty body
        "pay:-alice",       # leading hyphen
        "pay:Alice",        # uppercase
        "pay:a..b",         # empty label
        "pay:" + "a" * 130,  # too long
    ],
)
def test_invalid_uris(uri):
    assert not is_valid_pay_uri(uri)
    with pytest.raises(ValueError):
        assert_valid_pay_uri(uri)
