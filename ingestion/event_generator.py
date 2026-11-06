"""
DRIFTGUARD Deterministic Synthetic Event Generator
Generates realistic, cryptographically signed streaming transaction events
with deterministic scenarios, statistical anomaly injection, and security attack simulations.
"""

import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Generator
import numpy as np
from config import settings
from ingestion.event_schema import TransactionEvent
from security.key_manager import KeyManager
from security.signature_verifier import SignatureVerifier
from simulation.scenarios import ScenarioType, SCENARIO_CONFIGS


ANOMALY_CANDIDATES = [
    ScenarioType.AMOUNT_SPIKE,
    ScenarioType.VELOCITY_BURST,
    ScenarioType.DEVICE_SWITCH,
    ScenarioType.NETWORK_HOP,
]


class StreamEventGenerator:
    """
    Deterministic synthetic transaction stream generator.
    Creates validly signed events by default, with deliberate injection hooks
    for security attacks, statistical anomalies, and concept drift.
    """

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        key_id: str = settings.DEFAULT_KEY_ID,
        seed: int = settings.SIMULATION_SEED,
    ):
        self.key_manager = key_manager or KeyManager()
        self.key_id = key_id
        self.private_key, self.public_key = self.key_manager.load_or_create_default_key(key_id)
        self.rng = np.random.default_rng(seed)

        # Baseline client profiles for realistic state tracking
        self.accounts = [f"acc_{i:04d}" for i in range(1, 101)]
        self.devices_by_account = {acc: f"dev_{acc}_{self.rng.integers(100, 999)}" for acc in self.accounts}
        self.asns_by_account = {acc: int(self.rng.choice([15169, 16509, 13335, 7922])) for acc in self.accounts}
        self.current_sim_time = datetime.now(timezone.utc)
        self._real_rows = None
        self._real_idx = 0

    def _get_real_sample_row(self) -> Optional[Dict[str, Any]]:
        """Safely fetches a real row from the IEEE-CIS raw dataset if present."""
        ieee_file = settings.RAW_DATA_DIR / "ieee_cis" / "train_transaction.csv"
        if not ieee_file.exists():
            return None
        if self._real_rows is None:
            try:
                import pandas as pd
                cols = ["TransactionID", "TransactionDT", "TransactionAmt", "card1", "isFraud"]
                df = pd.read_csv(ieee_file, nrows=1000, usecols=cols)
                self._real_rows = df.to_dict(orient="records")
                self._real_idx = 0
            except Exception:
                self._real_rows = []
                return None
        if self._real_rows:
            row = self._real_rows[self._real_idx % len(self._real_rows)]
            self._real_idx += 1
            return row
        return None

    def generate_single_event(
        self,
        scenario: ScenarioType = ScenarioType.NORMAL,
        account_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        tamper_signature: bool = False,
    ) -> TransactionEvent:
        """Generates a single TransactionEvent corresponding to the designated scenario."""
        scenario_enum = ScenarioType(scenario) if not isinstance(scenario, ScenarioType) else scenario
        cfg = SCENARIO_CONFIGS.get(scenario_enum, SCENARIO_CONFIGS[ScenarioType.NORMAL])
        acc = account_id or str(self.rng.choice(self.accounts))

        # Determine Event Timestamp
        if timestamp:
            event_timestamp = timestamp
        else:
            event_timestamp = datetime.now(timezone.utc)
        self.current_sim_time = event_timestamp

        # Determine Amount
        mean_amt = cfg.get("mean_amount", 50.0)
        std_amt = cfg.get("amount_std", 15.0)
        amount = max(0.50, float(np.round(self.rng.normal(loc=mean_amt, scale=std_amt), 2)))

        # Determine Device & Session
        dev_stability = cfg.get("device_stability", 0.98)
        if self.rng.uniform() < dev_stability:
            device_id = self.devices_by_account[acc]
        else:
            device_id = f"dev_unrecognized_{self.rng.integers(10000, 99999)}"

        session_id = f"sess_{acc}_{secrets.token_hex(4)}"

        # Determine Network Context
        net_stability = cfg.get("network_stability", 0.99)
        if self.rng.uniform() < net_stability:
            asn = self.asns_by_account[acc]
            is_vpn = False
            ip_addr = f"198.51.{self.rng.integers(1, 254)}.{self.rng.integers(1, 254)}"
        else:
            asn = int(self.rng.choice([9009, 20473, 62240]))  # Known VPN / Datacenter ASNs
            is_vpn = True
            ip_addr = f"185.220.{self.rng.integers(1, 254)}.{self.rng.integers(1, 254)}"

        # Velocity
        if scenario == ScenarioType.VELOCITY_BURST:
            velocity = float(self.rng.integers(6, 18))
        else:
            velocity = float(self.rng.integers(1, 4))

        event_id = f"evt_{uuid.uuid4().hex[:16]}"
        nonce = secrets.token_hex(16)

        # Check for Real Data Replay
        dataset_source = "synthetic"
        if scenario_enum == ScenarioType.REAL_DATA_REPLAY:
            real_row = self._get_real_sample_row()
            if real_row:
                amount = float(real_row.get("TransactionAmt", amount))
                transaction_id = f"tx_ieee_{real_row.get('TransactionID')}"
                dataset_source = "ieee_cis_replay"
                synthetic_meta = {
                    "scenario": scenario_enum.value,
                    "is_real_data": True,
                    "source_tx_id": int(real_row.get("TransactionID", 0)),
                    "ground_truth_fraud": int(real_row.get("isFraud", 0)),
                    "account_id": acc,
                }
            else:
                transaction_id = f"tx_{acc}_{secrets.token_hex(6)}"
                dataset_source = "synthetic_fallback"
                synthetic_meta = {
                    "scenario": scenario_enum.value,
                    "fallback": True,
                    "notice": "Download IEEE-CIS dataset via Kaggle to replay authentic competition transactions.",
                    "account_id": acc,
                }
        else:
            transaction_id = f"tx_{acc}_{secrets.token_hex(6)}"
            synthetic_meta = {
                "scenario": scenario_enum.value,
                "is_injected_anomaly": cfg.get("is_anomaly", False),
                "description": cfg.get("description", ""),
                "account_id": acc,
            }

        # Construct raw event
        temp_event = TransactionEvent(
            event_id=event_id,
            transaction_id=transaction_id,
            timestamp=self.current_sim_time,
            device_id=device_id,
            session_id=session_id,
            key_id=self.key_id,
            nonce=nonce,
            amount=amount,
            signature="placeholder_signature_32_chars_long_minimum",
            transaction_velocity=velocity,
            device_context={"is_mobile": bool(self.rng.choice([True, False]))},
            ip_context={"ip_address": ip_addr, "is_vpn": is_vpn},
            asn=asn,
            dataset_source=dataset_source,
            synthetic_metadata=synthetic_meta,
        )

        # Cryptographically sign canonical bytes
        valid_signature = SignatureVerifier.sign_event(temp_event, self.private_key)

        should_tamper = tamper_signature or (scenario_enum == ScenarioType.TAMPERED_SIGNATURE)
        if should_tamper:
            # Adversary alters signature or payload without valid private key
            corrupted_sig = "deadbeef" * 8
            final_signature = corrupted_sig
        else:
            final_signature = valid_signature

        # Return event with authoritative signature
        return TransactionEvent(
            **{**temp_event.model_dump(), "signature": final_signature}
        )

    def generate_stream(
        self,
        count: int = 100,
        scenario: ScenarioType = ScenarioType.NORMAL,
        anomaly_ratio: float = 0.05,
    ) -> Generator[TransactionEvent, None, None]:
        """Generates a sequential stream of events with probabilistic anomaly injection."""
        # Monotonic timestamps spanning recent window within allowable freshness
        base_time = datetime.now(timezone.utc) - timedelta(seconds=min(240, count * 2))
        sim_time = base_time
        time_step = min(240.0 / max(1, count), 2.0)

        scenario_enum = ScenarioType(scenario) if not isinstance(scenario, ScenarioType) else scenario

        if scenario_enum == ScenarioType.REPLAY_ATTACK:
            # Yield alternating valid event followed immediately by its duplicate replay
            last_event = None
            for idx in range(count):
                sim_time = sim_time + timedelta(seconds=time_step)
                now = datetime.now(timezone.utc)
                if sim_time > now:
                    sim_time = now

                if idx % 2 == 1 and last_event is not None:
                    # Replay exact previous event
                    yield last_event
                else:
                    last_event = self.generate_single_event(scenario=ScenarioType.NORMAL, timestamp=sim_time)
                    yield last_event
            return

        for _ in range(count):
            sim_time = sim_time + timedelta(seconds=time_step)
            now = datetime.now(timezone.utc)
            if sim_time > now:
                sim_time = now

            if self.rng.uniform() < anomaly_ratio:
                # Randomly pick an anomaly scenario
                idx = int(self.rng.integers(0, len(ANOMALY_CANDIDATES)))
                injected_scenario = ANOMALY_CANDIDATES[idx]
                yield self.generate_single_event(scenario=injected_scenario, timestamp=sim_time)
            else:
                yield self.generate_single_event(scenario=scenario, timestamp=sim_time)
