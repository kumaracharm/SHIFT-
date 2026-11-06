"""
DRIFTGUARD Event Schema
Strongly validated Pydantic model for incoming transaction events.
Ensures strict UTC timestamps, non-empty identifiers, positive amounts,
and clean separation between source dataset attributes and synthetic metadata.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
import json
from pydantic import BaseModel, Field, field_validator, model_validator


class TransactionEvent(BaseModel):
    """
    Validated event representation for real-time ingestion, security, and ML scoring.
    """
    event_id: str = Field(..., min_length=1, description="Unique event identifier (UUID or deterministic ID)")
    transaction_id: str = Field(..., min_length=1, description="Core business transaction identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of the transaction occurrence")
    device_id: str = Field(..., min_length=1, description="Client device hardware/browser fingerprint identifier")
    session_id: str = Field(..., min_length=1, description="Client session identifier")
    key_id: str = Field(..., min_length=1, description="Identifier of the public key for cryptographic verification")
    nonce: str = Field(..., min_length=8, description="Cryptographic nonce to prevent replay attacks")
    amount: float = Field(..., gt=0.0, description="Transaction monetary amount; must be strictly positive")
    signature: str = Field(..., min_length=32, description="Ed25519 signature in hex format (or base64)")

    # Optional Contextual & Payment Telemetry
    sender_id: Optional[str] = Field(default=None, description="UPI Sender/Payer identifier (e.g. USER_1042)")
    receiver_id: Optional[str] = Field(default=None, description="UPI Receiver/Payee identifier (e.g. MERCHANT_208)")
    location: Optional[str] = Field(default=None, description="Geographical transaction location (e.g. Bengaluru)")
    payment_method: Optional[str] = Field(default="UPI", description="Payment protocol or rail (UPI, CARD, NETBANKING)")
    currency: Optional[str] = Field(default="INR", description="Transaction currency code")
    transaction_velocity: Optional[float] = Field(default=None, description="Rolling count or rate of transactions")
    device_context: Optional[Dict[str, Any]] = Field(default=None, description="Device attributes (e.g. OS, browser, is_mobile)")
    ip_context: Optional[Dict[str, Any]] = Field(default=None, description="Network context (e.g. IP address, country, is_vpn)")
    asn: Optional[Union[int, str]] = Field(default=None, description="Autonomous System Number")
    
    # Provenance and Synthetic Extension Metadata
    dataset_source: str = Field(default="synthetic", description="Source indicator: 'synthetic', 'ulb', or 'ieee'")
    synthetic_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata distinguishing synthetic simulations, scenario names, and labels"
    )

    # SHIFT provenance field — strictly required for data separation
    event_source: Optional[str] = Field(
        default="SYNTHETIC_UPI_SIMULATION",
        description=(
            "Provenance marker: 'SYNTHETIC_UPI_SIMULATION' for all generated UPI events, "
            "'IEEE_CIS_HISTORICAL' for IEEE-CIS dataset replay events. "
            "These two populations are NEVER mixed in analysis."
        ),
    )

    @field_validator("timestamp")
    @classmethod
    def enforce_utc_timestamp(cls, v: datetime) -> datetime:
        """Enforce UTC timezone; convert naive timestamps to UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("Transaction amount must be strictly greater than zero.")
        return round(float(v), 4)

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Creates a deterministic dictionary of all security-relevant payload fields.
        CRITICAL: The 'signature' field itself is strictly excluded.
        """
        data: Dict[str, Any] = {
            "event_id": self.event_id,
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp.isoformat(),
            "device_id": self.device_id,
            "session_id": self.session_id,
            "key_id": self.key_id,
            "nonce": self.nonce,
            "amount": self.amount,
            "dataset_source": self.dataset_source,
        }

        if self.event_source is not None:
            data["event_source"] = self.event_source

        # Include optional fields deterministically if provided
        if self.sender_id is not None:
            data["sender_id"] = self.sender_id
        if self.receiver_id is not None:
            data["receiver_id"] = self.receiver_id
        if self.location is not None:
            data["location"] = self.location
        if self.payment_method is not None:
            data["payment_method"] = self.payment_method
        if self.currency is not None:
            data["currency"] = self.currency
        if self.transaction_velocity is not None:
            data["transaction_velocity"] = round(float(self.transaction_velocity), 4)
        if self.device_context is not None:
            data["device_context"] = self.device_context
        if self.ip_context is not None:
            data["ip_context"] = self.ip_context
        if self.asn is not None:
            data["asn"] = str(self.asn)

        return data

    def get_canonical_bytes(self) -> bytes:
        """
        Produces exact UTF-8 encoded canonical JSON bytes with sorted keys
        and standard separators (no unnecessary spaces).
        """
        canonical_dict = self.to_canonical_dict()
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return canonical_json.encode("utf-8")

