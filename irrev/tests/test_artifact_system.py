from __future__ import annotations

from pathlib import Path

import pytest

from irrev.artifact.content_store import ContentStore
from irrev.artifact.plan_manager import PlanManager
from irrev.artifact.risk import RiskClass


def _make_tmp_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "content"
    vault.mkdir(parents=True, exist_ok=True)
    return vault


def test_content_store_roundtrip_and_verify(tmp_path: Path) -> None:
    irrev_dir = tmp_path / ".irrev"
    store = ContentStore(irrev_dir)

    content_id = store.store({"a": 1, "b": {"c": True}})
    assert store.exists(content_id)
    assert store.verify(content_id)
    assert store.get_json(content_id) == {"a": 1, "b": {"c": True}}


def test_plan_lifecycle_external_requires_approval(tmp_path: Path) -> None:
    vault = _make_tmp_vault(tmp_path)
    mgr = PlanManager(vault)

    plan_id = mgr.propose(
        "neo4j.load",
        {"http_uri": "http://example", "database": "irrev", "mode": "sync"},
        "agent:test",
        delegate_to="handler:neo4j",
    )

    assert mgr.validate(plan_id)
    snap = mgr.ledger.snapshot(plan_id)
    assert snap is not None
    assert snap.status == "validated"
    assert snap.computed_risk_class == RiskClass.EXTERNAL_SIDE_EFFECT
    assert snap.requires_approval() is True

    approval_id = mgr.approve(plan_id, "human:test", scope="neo4j-load")
    snap = mgr.ledger.snapshot(plan_id)
    assert snap is not None
    assert snap.status == "approved"
    assert snap.approval_artifact_id == approval_id

    def handler(_content: dict) -> dict:
        return {
            "ok": True,
            "erasure_cost": {"notes": 0, "edges": 0, "files": 0, "bytes_erased": 0, "details": {}},
            "creation_summary": {"notes": 0, "edges": 0, "files": 0, "bytes_written": 0, "details": {}},
        }

    result_id = mgr.execute(plan_id, "handler:neo4j", handler=handler)
    snap = mgr.ledger.snapshot(plan_id)
    assert snap is not None
    assert snap.status == "executed"
    assert snap.result_artifact_id == result_id

    approval_snap = mgr.ledger.snapshot(approval_id)
    assert approval_snap is not None
    assert approval_snap.artifact_type == "approval"


def test_force_ack_required_for_destructive(tmp_path: Path) -> None:
    vault = _make_tmp_vault(tmp_path)
    mgr = PlanManager(vault)

    plan_id = mgr.propose(
        "neo4j.load",
        {"http_uri": "http://example", "database": "irrev", "mode": "rebuild"},
        "agent:test",
        delegate_to="handler:neo4j",
    )
    assert mgr.validate(plan_id)

    with pytest.raises(ValueError, match="force_ack"):
        mgr.approve(plan_id, "human:test", scope="neo4j-rebuild", force_ack=False)

    approval_id = mgr.approve(plan_id, "human:test", scope="neo4j-rebuild", force_ack=True)
    assert isinstance(approval_id, str) and approval_id

