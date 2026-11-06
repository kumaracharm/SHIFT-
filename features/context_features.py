"""
DRIFTGUARD Context Feature Extractor
Extracts device stability, session continuity, and network telemetry indicators.
"""

from typing import Dict, Set, Optional
from ingestion.event_schema import TransactionEvent


class ContextFeatureExtractor:
    """
    Tracks session and network stability across streaming events.
    Maintains bounded state maps for device associations and IP/ASN transitions.
    """

    def __init__(self, max_entities: int = 1000):
        self.max_entities = max_entities
        # session_id -> device_id
        self._session_to_device: Dict[str, str] = {}
        # session_id -> last_asn
        self._session_to_asn: Dict[str, str] = {}
        # session_id -> transaction count
        self._session_counts: Dict[str, int] = {}

    def extract_features(self, event: TransactionEvent) -> Dict[str, float]:
        """Calculates device, session, and network consistency scores."""
        sess = event.session_id
        dev = event.device_id
        asn_val = str(event.asn) if event.asn is not None else "unknown"

        # 1. Device consistency for this session
        known_dev = self._session_to_device.get(sess)
        if known_dev is None:
            device_consistency = 1.0  # First event in session is consistent by definition
        elif known_dev == dev:
            device_consistency = 1.0
        else:
            device_consistency = 0.0  # Inconsistent: session switched devices mid-stream

        # 2. Session event count & stability
        sess_count = self._session_counts.get(sess, 0) + 1
        session_consistency = 1.0 if sess_count < 20 else 0.5  # Excessively prolonged session may indicate hijacking

        # 3. Network change & VPN risk flag
        known_asn = self._session_to_asn.get(sess)
        asn_changed = 1.0 if (known_asn is not None and known_asn != asn_val and asn_val != "unknown") else 0.0

        is_vpn = 0.0
        if event.ip_context and isinstance(event.ip_context, dict):
            if event.ip_context.get("is_vpn") is True:
                is_vpn = 1.0

        network_risk_flag = max(asn_changed, is_vpn)

        # Update bounded tracking state
        if len(self._session_to_device) >= self.max_entities:
            # Prune arbitrary key to bound memory
            del self._session_to_device[next(iter(self._session_to_device))]
            if sess in self._session_to_asn:
                del self._session_to_asn[sess]
            if sess in self._session_counts:
                del self._session_counts[sess]

        self._session_to_device[sess] = dev
        self._session_to_asn[sess] = asn_val
        self._session_counts[sess] = sess_count

        return {
            "device_consistency": device_consistency,
            "session_consistency": session_consistency,
            "network_risk_flag": network_risk_flag,
        }

