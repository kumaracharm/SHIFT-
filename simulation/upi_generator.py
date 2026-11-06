"""
DRIFTGUARD UPI Synthetic Transaction Stream Generator
Generates realistic, cryptographically signed streaming UPI payment transactions
representing a fictional real-time Indian payment infrastructure.
Strictly synthetic identities and simulated banking rails.
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

# Fictional Indian Metros and Network ASNs
INDIAN_CITIES = ["Bengaluru", "Mumbai", "Delhi-NCR", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]
JUMP_CITIES = ["Lagos", "Bucharest", "Panama City", "Frankfurt", "Saint Petersburg"]

INDIAN_ASNS = {
    "Jio Digital": 55836,
    "Airtel Broadband": 45609,
    "ACT Fibernet": 24309,
    "Tata Teleservices": 4755,
}
SUSPICIOUS_ASNS = {
    "NordVPN / Hosting": 9009,
    "Mullvad Datacenter": 20473,
    "Tor Exit Relay": 62240,
}

POPULAR_MERCHANTS = [
    ("MERCHANT_208", "swiggy@icici", "Swiggy Food Delivery", "KNOWN_MERCHANT"),
    ("MERCHANT_105", "zomato@hdfcbank", "Zomato Dine", "KNOWN_MERCHANT"),
    ("MERCHANT_312", "amazonpay@apl", "Amazon India", "KNOWN_MERCHANT"),
    ("MERCHANT_404", "flipkart@axis", "Flipkart Commerce", "KNOWN_MERCHANT"),
    ("MERCHANT_519", "dmart@sbi", "Avenue Supermarts", "KNOWN_MERCHANT"),
    ("MERCHANT_602", "uber@ybl", "Uber Rides India", "KNOWN_MERCHANT"),
    ("MERCHANT_710", "tataneu@hdfcbank", "Tata Digital", "KNOWN_MERCHANT"),
]


class UPITransactionGenerator:
    """
    Simulates high-velocity, realistic UPI payment events.
    Signs all canonical event payloads with Ed25519 asymmetric cryptography.
    Injects deterministic fraud patterns, network hops, device shifts, and MITM attacks.
    """

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        key_id: str = settings.DEFAULT_KEY_ID,
        seed: int = 42,
    ):
        self.key_manager = key_manager or KeyManager()
        self.key_id = key_id
        self.private_key, self.public_key = self.key_manager.load_or_create_default_key(key_id)
        self.rng = np.random.default_rng(seed)

        # Baseline Client Entities
        self.users = [f"USER_{1000 + i}" for i in range(1, 151)]
        self.devices_by_user = {
            u: f"dev_android_{secrets.token_hex(4)}" for u in self.users
        }
        self.locations_by_user = {
            u: str(self.rng.choice(INDIAN_CITIES)) for u in self.users
        }
        self.asn_by_user = {
            u: int(self.rng.choice(list(INDIAN_ASNS.values()))) for u in self.users
        }
        self.vpa_by_user = {
            u: f"{u.lower()}@okaxis" for u in self.users
        }

        # Stateful sequence counters
        self.tx_counter = 1
        self.last_tx_time_by_user: Dict[str, datetime] = {}
        self.tx_count_by_user_window: Dict[str, int] = {u: 0 for u in self.users}

    def generate_single_event(
        self,
        scenario: ScenarioType = ScenarioType.UPI_NORMAL,
        sender_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        tamper_signature: bool = False,
    ) -> TransactionEvent:
        """Constructs a single realistic, cryptographically validated UPI payment event."""
        scenario_enum = ScenarioType(scenario) if not isinstance(scenario, ScenarioType) else scenario
        cfg = SCENARIO_CONFIGS.get(scenario_enum, SCENARIO_CONFIGS.get(ScenarioType.UPI_NORMAL, {}))

        sender = sender_id or str(self.rng.choice(self.users))
        event_time = timestamp or datetime.now(timezone.utc)

        # Calculate Transaction ID (Formatted UPI reference)
        date_str = event_time.strftime("%Y%m%d")
        tx_num = f"{self.tx_counter:06d}"
        self.tx_counter += 1
        transaction_id = f"UPI-{date_str}-{tx_num}"
        event_id = f"evt_{uuid.uuid4().hex[:16]}"
        nonce = secrets.token_hex(16)
        session_id = f"sess_{sender.lower()}_{secrets.token_hex(4)}"

        # Default Telemetry
        device_id = self.devices_by_user[sender]
        location = self.locations_by_user[sender]
        asn = self.asn_by_user[sender]
        is_vpn = False
        device_trust = "ESTABLISHED"
        payee_status = "KNOWN_MERCHANT"

        # Determine Receiver & VPA
        if self.rng.uniform() < 0.70:
            m_tuple = POPULAR_MERCHANTS[int(self.rng.integers(0, len(POPULAR_MERCHANTS)))]
            receiver = m_tuple[0]
            receiver_vpa = m_tuple[1]
            payee_status = m_tuple[3]
        else:
            rec_user = str(self.rng.choice(self.users))
            while rec_user == sender:
                rec_user = str(self.rng.choice(self.users))
            receiver = rec_user
            receiver_vpa = self.vpa_by_user[rec_user]
            payee_status = "PEER_TRANSFER"

        # Compute Amount based on scenario
        mean_amt = cfg.get("mean_amount", 850.0)
        std_amt = cfg.get("amount_std", 450.0)
        amount = max(10.0, float(np.round(self.rng.normal(loc=mean_amt, scale=std_amt), 2)))

        # Velocity tracking
        prev_time = self.last_tx_time_by_user.get(sender)
        if prev_time:
            time_delta = (event_time - prev_time).total_seconds()
            if time_delta < 60.0:
                self.tx_count_by_user_window[sender] = self.tx_count_by_user_window.get(sender, 0) + 1
            else:
                self.tx_count_by_user_window[sender] = 1
        else:
            self.tx_count_by_user_window[sender] = 1
        self.last_tx_time_by_user[sender] = event_time

        velocity = float(self.tx_count_by_user_window[sender])

        # Scenario Injections
        if scenario_enum in (ScenarioType.UPI_AMOUNT_SPIKE, ScenarioType.AMOUNT_SPIKE):
            amount = max(65000.0, float(np.round(self.rng.normal(loc=82500.0, scale=8000.0), 2)))

        elif scenario_enum in (ScenarioType.UPI_VELOCITY_BURST, ScenarioType.VELOCITY_BURST):
            velocity = float(self.rng.integers(7, 16))
            amount = float(self.rng.choice([1999.0, 4999.0, 9999.0]))
            receiver = "SUSPICIOUS_PAYEE_99"
            receiver_vpa = "fastcash99@fakeupi"
            payee_status = "SUSPICIOUS_MULE"

        elif scenario_enum == ScenarioType.UPI_NEW_PAYEE:
            receiver = f"NEW_VPA_{secrets.token_hex(3).upper()}"
            receiver_vpa = f"unverified_{secrets.token_hex(4)}@fakeupi"
            payee_status = "NEW_UNVERIFIED"
            amount = float(np.round(self.rng.normal(loc=34000.0, scale=4000.0), 2))

        elif scenario_enum in (ScenarioType.UPI_DEVICE_CHANGE, ScenarioType.DEVICE_SWITCH):
            device_id = f"dev_unrecognized_{secrets.token_hex(4)}"
            device_trust = "UNRECOGNIZED_HARDWARE"

        elif scenario_enum in (ScenarioType.UPI_LOCATION_JUMP, ScenarioType.NETWORK_HOP):
            location = str(self.rng.choice(JUMP_CITIES))
            asn = int(self.rng.choice(list(SUSPICIOUS_ASNS.values())))
            is_vpn = True

        elif scenario_enum == ScenarioType.UPI_MULE_RING:
            receiver = "CENTRAL_MULE_RING_01"
            receiver_vpa = "mulecluster01@mulebank"
            payee_status = "FLAGGED_MULE_ACCOUNT"
            amount = float(self.rng.choice([24999.0, 49999.0, 99999.0]))
            velocity = float(self.rng.integers(9, 20))

        synthetic_meta = {
            "scenario": scenario_enum.value,
            "sender_vpa": self.vpa_by_user[sender],
            "receiver_vpa": receiver_vpa,
            "payee_status": payee_status,
            "device_trust": device_trust,
            "is_anomaly": cfg.get("is_anomaly", False),
            "description": cfg.get("description", "UPI payment transaction"),
        }

        # Construct validated TransactionEvent
        temp_event = TransactionEvent(
            event_id=event_id,
            transaction_id=transaction_id,
            timestamp=event_time,
            device_id=device_id,
            session_id=session_id,
            key_id=self.key_id,
            nonce=nonce,
            amount=amount,
            signature="placeholder_sig_32_characters_minimum",
            sender_id=sender,
            receiver_id=receiver,
            location=location,
            payment_method="UPI",
            currency="INR",
            transaction_velocity=velocity,
            device_context={
                "os": "Android 14 (Knox Verified)" if "android" in device_id else "iOS 17.4",
                "device_trust": device_trust,
                "is_mobile": True,
            },
            ip_context={
                "ip_address": f"103.{self.rng.integers(10, 250)}.{self.rng.integers(1, 254)}.{self.rng.integers(1, 254)}",
                "city": location,
                "is_vpn": is_vpn,
            },
            asn=asn,
            dataset_source="synthetic_upi",
            synthetic_metadata=synthetic_meta,
        )

        # Cryptographically sign canonical bytes using Ed25519
        valid_signature = SignatureVerifier.sign_event(temp_event, self.private_key)

        should_tamper = tamper_signature or (scenario_enum in (ScenarioType.UPI_TAMPERED, ScenarioType.TAMPERED_SIGNATURE))
        if should_tamper:
            final_signature = "deadbeef" * 8  # Corrupted cryptographic signature
        else:
            final_signature = valid_signature

        return TransactionEvent(
            **{**temp_event.model_dump(), "signature": final_signature}
        )

    def generate_stream(
        self,
        count: int = 20,
        scenario: ScenarioType = ScenarioType.UPI_NORMAL,
        anomaly_ratio: float = 0.05,
    ) -> Generator[TransactionEvent, None, None]:
        """Yields a continuous stream of signed events."""
        base_time = datetime.now(timezone.utc) - timedelta(seconds=min(120, count * 2))
        sim_time = base_time
        time_step = min(120.0 / max(1, count), 1.5)

        scenario_enum = ScenarioType(scenario) if not isinstance(scenario, ScenarioType) else scenario

        if scenario_enum in (ScenarioType.UPI_REPLAY_ATTACK, ScenarioType.REPLAY_ATTACK):
            last_event = None
            for idx in range(count):
                sim_time += timedelta(seconds=time_step)
                now = datetime.now(timezone.utc)
                if sim_time > now:
                    sim_time = now

                if idx % 2 == 1 and last_event is not None:
                    # Retransmit exact duplicate of previous signed authorization
                    yield last_event
                else:
                    last_event = self.generate_single_event(scenario=ScenarioType.UPI_NORMAL, timestamp=sim_time)
                    yield last_event
            return

        for _ in range(count):
            sim_time += timedelta(seconds=time_step)
            now = datetime.now(timezone.utc)
            if sim_time > now:
                sim_time = now

            if self.rng.uniform() < anomaly_ratio and scenario_enum == ScenarioType.UPI_NORMAL:
                anomaly_candidates = [
                    ScenarioType.UPI_AMOUNT_SPIKE,
                    ScenarioType.UPI_VELOCITY_BURST,
                    ScenarioType.UPI_NEW_PAYEE,
                    ScenarioType.UPI_DEVICE_CHANGE,
                ]
                injected = anomaly_candidates[int(self.rng.integers(0, len(anomaly_candidates)))]
                yield self.generate_single_event(scenario=injected, timestamp=sim_time)
            else:
                yield self.generate_single_event(scenario=scenario_enum, timestamp=sim_time)

