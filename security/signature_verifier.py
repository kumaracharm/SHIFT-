"""
DRIFTGUARD Cryptographic Signature Verifier
Implements Ed25519 signature generation and verification over canonical event byte representations.
"""

from typing import Union, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
from ingestion.event_schema import TransactionEvent


class SignatureVerifier:
    """Verifies Ed25519 digital signatures on incoming canonical transaction events."""

    @staticmethod
    def sign_event(event: TransactionEvent, private_key: ed25519.Ed25519PrivateKey) -> str:
        """
        Signs the canonical representation of an event with the given private key.
        Returns the signature as a lowercase hexadecimal string.
        """
        canonical_bytes = event.get_canonical_bytes()
        signature_bytes = private_key.sign(canonical_bytes)
        return signature_bytes.hex()

    @staticmethod
    def verify_event(event: TransactionEvent, public_key: ed25519.Ed25519PublicKey) -> Tuple[bool, str]:
        """
        Verifies the event's Ed25519 signature against its canonical payload representation.
        Returns (True, "VALID_SIGNATURE") or (False, reason).
        """
        try:
            sig_bytes = bytes.fromhex(event.signature)
        except ValueError:
            return False, "INVALID_HEX_SIGNATURE_FORMAT"

        canonical_bytes = event.get_canonical_bytes()

        try:
            public_key.verify(sig_bytes, canonical_bytes)
            return True, "VALID_SIGNATURE"
        except InvalidSignature:
            return False, "SIGNATURE_VERIFICATION_FAILED"
        except Exception as exc:
            return False, f"VERIFICATION_ERROR: {str(exc)}"

