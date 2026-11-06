"""
DRIFTGUARD Cryptographic Key Manager
Manages Ed25519 key generation, storage, and trusted public key registry.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from config import settings


class KeyManager:
    """
    Handles Ed25519 private/public key lifecycles and maintains trusted public key mappings.
    Private keys are only used for signing outgoing/simulated transactions.
    """

    def __init__(self, keys_dir: Optional[Path] = None):
        self.keys_dir = keys_dir or settings.KEYS_DIR
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self._trusted_public_keys: Dict[str, ed25519.Ed25519PublicKey] = {}
        self._private_keys: Dict[str, ed25519.Ed25519PrivateKey] = {}

    def generate_key_pair(self, key_id: str = settings.DEFAULT_KEY_ID) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Generates a new Ed25519 key pair, registers it locally, and returns the pair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        self._private_keys[key_id] = private_key
        self._trusted_public_keys[key_id] = public_key

        return private_key, public_key

    def save_key_pair(
        self,
        key_id: str,
        private_key: ed25519.Ed25519PrivateKey,
        public_key: ed25519.Ed25519PublicKey,
    ) -> Tuple[Path, Path]:
        """Saves key pair securely to disk in PEM format."""
        priv_path = self.keys_dir / f"{key_id}_private.pem"
        pub_path = self.keys_dir / f"{key_id}_public.pem"

        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        priv_path.write_bytes(priv_pem)
        pub_path.write_bytes(pub_pem)

        return priv_path, pub_path

    def load_or_create_default_key(
        self, key_id: str = settings.DEFAULT_KEY_ID
    ) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Loads default key pair from disk if present, or creates and stores a new one."""
        priv_path = self.keys_dir / f"{key_id}_private.pem"
        pub_path = self.keys_dir / f"{key_id}_public.pem"

        if priv_path.exists() and pub_path.exists():
            private_key = serialization.load_pem_private_key(
                priv_path.read_bytes(),
                password=None,
            )
            public_key = serialization.load_pem_public_key(
                pub_path.read_bytes(),
            )
            assert isinstance(private_key, ed25519.Ed25519PrivateKey)
            assert isinstance(public_key, ed25519.Ed25519PublicKey)
            self._private_keys[key_id] = private_key
            self._trusted_public_keys[key_id] = public_key
            return private_key, public_key

        private_key, public_key = self.generate_key_pair(key_id)
        self.save_key_pair(key_id, private_key, public_key)
        return private_key, public_key

    def register_public_key(self, key_id: str, public_key: ed25519.Ed25519PublicKey) -> None:
        """Registers a trusted public key in memory."""
        self._trusted_public_keys[key_id] = public_key

    def register_public_key_pem(self, key_id: str, pem_bytes: bytes) -> None:
        """Parses and registers a trusted public key from PEM bytes."""
        public_key = serialization.load_pem_public_key(pem_bytes)
        assert isinstance(public_key, ed25519.Ed25519PublicKey)
        self.register_public_key(key_id, public_key)

    def get_public_key(self, key_id: str) -> Optional[ed25519.Ed25519PublicKey]:
        """Retrieves a trusted public key by ID, loading from disk if needed."""
        if key_id not in self._trusted_public_keys:
            pub_path = self.keys_dir / f"{key_id}_public.pem"
            if pub_path.exists():
                try:
                    self.register_public_key_pem(key_id, pub_path.read_bytes())
                except Exception:
                    pass
        return self._trusted_public_keys.get(key_id)

    def get_private_key(self, key_id: str) -> Optional[ed25519.Ed25519PrivateKey]:
        """Retrieves a local private key by ID for signing."""
        return self._private_keys.get(key_id)

