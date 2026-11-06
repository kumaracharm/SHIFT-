"""
DRIFTGUARD Simulation Scenarios
Deterministic scenario definitions for streaming fraud injection, concept drift, and security attacks.
"""

from enum import Enum
from typing import Dict, Any


class ScenarioType(str, Enum):
    NORMAL = "normal"
    REAL_DATA_REPLAY = "real_data_replay"
    AMOUNT_SPIKE = "amount_spike"
    VELOCITY_BURST = "velocity_burst"
    LOW_AND_SLOW = "low_and_slow"
    DEVICE_SWITCH = "device_switch"
    NETWORK_HOP = "network_hop"
    FRAUD_PATTERN_SHIFT = "fraud_pattern_shift"
    TAMPERED_SIGNATURE = "tampered_signature"
    REPLAY_ATTACK = "replay_attack"

    # UPI Specific Scenarios
    UPI_NORMAL = "upi_normal"
    UPI_AMOUNT_SPIKE = "upi_amount_spike"
    UPI_VELOCITY_BURST = "upi_velocity_burst"
    UPI_NEW_PAYEE = "upi_new_payee"
    UPI_DEVICE_CHANGE = "upi_device_change"
    UPI_LOCATION_JUMP = "upi_location_jump"
    UPI_REPLAY_ATTACK = "upi_replay_attack"
    UPI_TAMPERED = "upi_tampered"
    UPI_MULE_RING = "upi_mule_ring"


SCENARIO_CONFIGS: Dict[ScenarioType, Dict[str, Any]] = {
    ScenarioType.NORMAL: {
        "description": "Standard legitimate transaction baseline with typical amounts and intervals.",
        "mean_amount": 45.0,
        "amount_std": 20.0,
        "mean_interval_sec": 30.0,
        "device_stability": 0.98,
        "network_stability": 0.99,
        "is_anomaly": False,
    },
    ScenarioType.REAL_DATA_REPLAY: {
        "description": "Streaming replay of genuine merchant transactions using real TransactionDT chronological intervals and authentic amounts.",
        "mean_amount": 135.0,
        "amount_std": 240.0,
        "mean_interval_sec": 12.0,
        "device_stability": 0.95,
        "network_stability": 0.95,
        "is_anomaly": False,
    },
    ScenarioType.AMOUNT_SPIKE: {
        "description": "Sudden astronomical purchase amount exceeding 20x historical device median.",
        "mean_amount": 3500.0,
        "amount_std": 500.0,
        "mean_interval_sec": 30.0,
        "device_stability": 0.90,
        "network_stability": 0.90,
        "is_anomaly": True,
    },
    ScenarioType.VELOCITY_BURST: {
        "description": "Rapid succession of transactions within sub-minute intervals (card testing/burst).",
        "mean_amount": 25.0,
        "amount_std": 10.0,
        "mean_interval_sec": 1.5,
        "device_stability": 0.95,
        "network_stability": 0.95,
        "is_anomaly": True,
    },
    ScenarioType.LOW_AND_SLOW: {
        "description": "Subtle, micro-transactions designed to remain just below static detection thresholds.",
        "mean_amount": 4.99,
        "amount_std": 0.50,
        "mean_interval_sec": 45.0,
        "device_stability": 0.90,
        "network_stability": 0.85,
        "is_anomaly": True,
    },
    ScenarioType.DEVICE_SWITCH: {
        "description": "Transaction originating from an unrecognized hardware device/browser fingerprint.",
        "mean_amount": 180.0,
        "amount_std": 40.0,
        "mean_interval_sec": 20.0,
        "device_stability": 0.0,  # Forces device mismatch
        "network_stability": 0.90,
        "is_anomaly": True,
    },
    ScenarioType.NETWORK_HOP: {
        "description": "Sudden geographical hop or hosting provider / anonymous VPN ASN.",
        "mean_amount": 120.0,
        "amount_std": 30.0,
        "mean_interval_sec": 25.0,
        "device_stability": 0.80,
        "network_stability": 0.0,  # Forces network anomaly
        "is_anomaly": True,
    },
    ScenarioType.FRAUD_PATTERN_SHIFT: {
        "description": "Concept drift: new emerging fraud modus operandi with irregular midnight amounts.",
        "mean_amount": 750.0,
        "amount_std": 150.0,
        "mean_interval_sec": 5.0,
        "device_stability": 0.50,
        "network_stability": 0.40,
        "is_anomaly": True,
    },
    ScenarioType.TAMPERED_SIGNATURE: {
        "description": "Adversary modifies payload amount in transit without valid private signing key.",
        "is_anomaly": True,
        "attack_type": "tamper",
    },
    ScenarioType.REPLAY_ATTACK: {
        "description": "Adversary intercepts and resends an identical valid event to double-spend.",
        "is_anomaly": True,
        "attack_type": "replay",
    },

    # UPI Stream Configurations
    ScenarioType.UPI_NORMAL: {
        "description": "Standard legitimate UPI P2M/P2P transfers with normal amounts, familiar payees, and trusted devices.",
        "mean_amount": 850.0,
        "amount_std": 450.0,
        "mean_interval_sec": 5.0,
        "device_stability": 0.99,
        "network_stability": 0.99,
        "is_anomaly": False,
    },
    ScenarioType.UPI_AMOUNT_SPIKE: {
        "description": "Sudden massive UPI fund transfer (₹65,000 to ₹95,000) breaching standard consumer velocity/amount limits.",
        "mean_amount": 78000.0,
        "amount_std": 12000.0,
        "mean_interval_sec": 8.0,
        "device_stability": 0.95,
        "network_stability": 0.90,
        "is_anomaly": True,
    },
    ScenarioType.UPI_VELOCITY_BURST: {
        "description": "High-frequency succession of rapid repeated payments to same VPA within seconds (account drain/card testing).",
        "mean_amount": 4999.0,
        "amount_std": 500.0,
        "mean_interval_sec": 1.2,
        "device_stability": 0.95,
        "network_stability": 0.95,
        "is_anomaly": True,
    },
    ScenarioType.UPI_NEW_PAYEE: {
        "description": "Large transfer to an unverified, newly created VPA handle with zero prior transaction history.",
        "mean_amount": 32000.0,
        "amount_std": 5000.0,
        "mean_interval_sec": 10.0,
        "device_stability": 0.90,
        "network_stability": 0.90,
        "is_anomaly": True,
    },
    ScenarioType.UPI_DEVICE_CHANGE: {
        "description": "UPI transfer executed immediately following device/SIM binding change on an untrusted hardware fingerprint.",
        "mean_amount": 15000.0,
        "amount_std": 3000.0,
        "mean_interval_sec": 15.0,
        "device_stability": 0.0,
        "network_stability": 0.85,
        "is_anomaly": True,
    },
    ScenarioType.UPI_LOCATION_JUMP: {
        "description": "Impossible travel: transaction initiated from international/distant IP minutes after local Bengaluru transaction.",
        "mean_amount": 12500.0,
        "amount_std": 2000.0,
        "mean_interval_sec": 20.0,
        "device_stability": 0.70,
        "network_stability": 0.0,
        "is_anomaly": True,
    },
    ScenarioType.UPI_REPLAY_ATTACK: {
        "description": "Adversary captures signed UPI authorization payload and retransmits it to execute duplicate debit.",
        "is_anomaly": True,
        "attack_type": "replay",
    },
    ScenarioType.UPI_TAMPERED: {
        "description": "Man-in-the-middle alters payment destination VPA or amount in flight without private key.",
        "is_anomaly": True,
        "attack_type": "tamper",
    },
    ScenarioType.UPI_MULE_RING: {
        "description": "Coordinated multi-account rapid fan-out transfers to centralized mule account cluster.",
        "mean_amount": 24500.0,
        "amount_std": 4000.0,
        "mean_interval_sec": 2.0,
        "device_stability": 0.40,
        "network_stability": 0.30,
        "is_anomaly": True,
    },
}

