"""
DRIFTGUARD Event Validator
Provides safe deserialization, boundary checks, and error formatting for transaction inputs.
"""

from typing import Dict, Any, Tuple, Optional
from pydantic import ValidationError
from ingestion.event_schema import TransactionEvent


class EventValidator:
    """Safely validates raw input dictionaries and converts them to TransactionEvent."""

    @staticmethod
    def validate_payload(payload: Dict[str, Any]) -> Tuple[bool, Optional[TransactionEvent], Optional[str]]:
        """
        Validates a dictionary against the TransactionEvent schema.
        Returns: (is_valid, event_instance_or_none, error_message_or_none)
        """
        try:
            event = TransactionEvent(**payload)
            return True, event, None
        except ValidationError as val_err:
            errors = val_err.errors()
            formatted_errors = [
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in errors
            ]
            return False, None, "; ".join(formatted_errors)
        except Exception as exc:
            return False, None, f"Unexpected validation failure: {str(exc)}"

