import os
from pathlib import Path
from typing import Tuple

from flask import current_app

from ..utils.crypto import CryptoManager


class EncryptedStorageService:
    def __init__(self, base_dir: str, crypto: CryptoManager) -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)
        self._crypto = crypto

    def _path_for(self, rel_path: str) -> Path:
        return (self._base / rel_path).resolve()

    def write_encrypted(self, rel_path: str, data: bytes, context: str) -> Tuple[str, int]:
        key_id, blob = self._crypto.encrypt(data, context.encode("utf-8"))
        path = self._path_for(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(blob)
        return key_id, len(blob)

    def read_decrypted(self, rel_path: str, key_id: str, context: str) -> bytes:
        path = self._path_for(rel_path)
        with open(path, "rb") as f:
            blob = f.read()
        return self._crypto.decrypt(key_id, blob, context.encode("utf-8"))


def get_storage_service() -> EncryptedStorageService:
    storage_dir = current_app.config["STORAGE_DIR"]
    crypto = CryptoManager(
        master_key_hex=current_app.config["MASTER_ENCRYPTION_KEY_HEX"],
        active_key_id=current_app.config["ACTIVE_ENCRYPTION_KEY_ID"],
    )
    return EncryptedStorageService(storage_dir, crypto)
