import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from binascii import unhexlify


class CryptoManager:
    def __init__(self, master_key_hex: str, active_key_id: str = "default") -> None:
        if not master_key_hex or len(master_key_hex) != 64:
            raise ValueError("MASTER_ENCRYPTION_KEY_HEX must be a 32-byte hex string (64 hex chars)")
        self._master_key = unhexlify(master_key_hex)
        self._active_key_id = active_key_id

    @property
    def active_key_id(self) -> str:
        return self._active_key_id

    def _derive_key(self, context: bytes) -> bytes:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=context)
        return hkdf.derive(self._master_key)

    def encrypt(self, plaintext: bytes, context: bytes) -> Tuple[str, bytes]:
        key = self._derive_key(context)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, context)
        return self._active_key_id, nonce + ciphertext

    def decrypt(self, key_id: str, data: bytes, context: bytes) -> bytes:
        # Currently single active key; key_id reserved for future rotations
        key = self._derive_key(context)
        aesgcm = AESGCM(key)
        nonce, ciphertext = data[:12], data[12:]
        return aesgcm.decrypt(nonce, ciphertext, context)
