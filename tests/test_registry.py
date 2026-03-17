from app.services.registry import AgentRegistry, AgentRecord
from datetime import datetime, timezone

def make_record(**kwargs):
    defaults = dict(
        agent_id="AGT-TEST-001", org_id="ORG-001", domain="FINTECH",
        payment_alias="pay:agent.test", endpoint=None,
        trust_tier="ORG_VERIFIED", protocol_versions=["1.0"],
        message_types=["QUERY", "VERIFY"], input_schemas=["A2A_MESSAGE_V1"],
        output_schemas=["TEST_RESULT_V1"], tools=[], max_latency_ms=1000,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(kwargs)
    return AgentRecord(**defaults)

def test_register_and_retrieve():
    reg = AgentRegistry()
    rec = reg.register(make_record())
    assert reg.get("AGT-TEST-001") == rec

def test_find_by_payment_alias():
    reg = AgentRegistry()
    reg.register(make_record())
    found = reg.find_by_alias("pay:agent.test")
    assert found is not None
    assert found.agent_id == "AGT-TEST-001"

def test_list_by_domain():
    reg = AgentRegistry()
    reg.register(make_record(agent_id="AGT-A", domain="FINTECH",
                              payment_alias="pay:a.test"))
    reg.register(make_record(agent_id="AGT-B", domain="COMPUTE",
                              payment_alias="pay:b.test"))
    results = reg.list_by_domain("FINTECH")
    assert any(r.agent_id == "AGT-A" for r in results)
    assert all(r.domain == "FINTECH" for r in results)
