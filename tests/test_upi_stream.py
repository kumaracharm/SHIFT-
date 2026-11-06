"""
DRIFTGUARD UPI Stream & Operator Controller Tests
Verifies synthetic UPI transaction generation, schema validation, Ed25519 integrity,
replay & tamper rejection, operator control state machine, decision logic, and CSV export.
"""

import pytest
from datetime import datetime, timezone
from storage.database import init_db, engine, SessionLocal
from ingestion.event_schema import TransactionEvent
from simulation.upi_generator import UPITransactionGenerator
from simulation.stream_controller import StreamController, StreamState
from simulation.scenarios import ScenarioType
from engine.event_service import EventProcessingService
from engine.decision_engine import DecisionType, DecisionEngine
from dashboard.services.dashboard_service import DashboardService


@pytest.fixture(scope="module")
def setup_db():
    init_db(engine)
    yield


def test_upi_transaction_generation(setup_db):
    gen = UPITransactionGenerator(seed=123)
    event = gen.generate_single_event(scenario=ScenarioType.UPI_NORMAL)

    assert isinstance(event, TransactionEvent)
    assert event.payment_method == "UPI"
    assert event.currency == "INR"
    assert event.amount > 0.0
    assert event.sender_id is not None
    assert event.receiver_id is not None
    assert event.location is not None
    assert len(event.signature) >= 64
    assert event.transaction_id.startswith("UPI-")


def test_upi_event_uniqueness(setup_db):
    gen = UPITransactionGenerator(seed=456)
    events = list(gen.generate_stream(count=10, scenario=ScenarioType.UPI_NORMAL))

    tx_ids = [e.transaction_id for e in events]
    event_ids = [e.event_id for e in events]
    nonces = [e.nonce for e in events]

    assert len(set(tx_ids)) == 10
    assert len(set(event_ids)) == 10
    assert len(set(nonces)) == 10


def test_upi_tamper_rejection(setup_db):
    gen = UPITransactionGenerator(seed=789)
    session = SessionLocal()
    try:
        service = EventProcessingService(session=session)
        # Generate tampered event
        event = gen.generate_single_event(scenario=ScenarioType.UPI_TAMPERED, tamper_signature=True)
        res = service.process_event(event)

        assert res.integrity_status == "REJECTED_BAD_SIG"
        assert res.decision == DecisionType.INTEGRITY_REJECTED
        assert DecisionType.to_action(res.decision) == "BLOCK"
    finally:
        session.close()


def test_upi_replay_rejection(setup_db):
    gen = UPITransactionGenerator(seed=999)
    session = SessionLocal()
    try:
        service = EventProcessingService(session=session)
        # Legitimate event
        event1 = gen.generate_single_event(scenario=ScenarioType.UPI_NORMAL)
        res1 = service.process_event(event1)
        assert res1.integrity_status == "VALID"

        # Direct duplicate replay
        res2 = service.process_event(event1)
        assert "REJECTED_REPLAY" in res2.integrity_status
        assert res2.decision == DecisionType.INTEGRITY_REJECTED
        assert DecisionType.to_action(res2.decision) == "BLOCK"
    finally:
        session.close()


def test_stream_controller_lifecycle(setup_db):
    controller = StreamController()
    
    # Ingest a batch of 5 UPI events
    results = controller.step(scenario=ScenarioType.UPI_NORMAL, count=5)
    assert len(results) == 5
    for r in results:
        assert r["integrity_status"] == "VALID"
        assert r["amount"] > 0.0

    # Ingest single anomaly
    spike_res = controller.trigger_single_scenario(scenario=ScenarioType.UPI_AMOUNT_SPIKE)
    assert spike_res["amount"] >= 50000.0


def test_csv_export(setup_db):
    controller = StreamController()
    controller.step(scenario=ScenarioType.UPI_NORMAL, count=3)

    csv_data = controller.export_csv(limit=50)
    assert "TransactionID" in csv_data
    assert "Sender" in csv_data
    assert "Receiver" in csv_data
    assert "Decision" in csv_data

