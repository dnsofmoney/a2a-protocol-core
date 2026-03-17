from app.services.resolver import FASResolver

def setup_resolver():
    return FASResolver()

def test_resolve_known_alias():
    r = setup_resolver().resolve("pay:agent.compute")
    assert r is not None
    assert r.preferred_rail in ["XRPL", "FEDNOW", "ACH", "INTERNAL_LEDGER"]

def test_resolve_unknown_returns_none():
    assert setup_resolver().resolve("pay:unknown.entity") is None

def test_signature_verification():
    res = setup_resolver()
    record = res.resolve("pay:agent.compute")
    assert res.verify(record) is True

def test_rail_selection_policy():
    res = setup_resolver()
    record = res.resolve("pay:agent.compute")
    ep = res.select_rail(record, policy={"allowed_rails": ["FEDNOW"]})
    assert ep.rail == "FEDNOW"

def test_all_seed_aliases_resolve():
    res = setup_resolver()
    for alias in ["pay:agent.compute", "pay:vendor.alpha", "pay:agent.analysis"]:
        assert res.resolve(alias) is not None
