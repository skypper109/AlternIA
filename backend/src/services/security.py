"""
Module de sécurité et de hachage de mots de passe pour alta_db.
Utilise PBKDF2-HMAC-SHA256 avec sel aléatoire (standard sécurisé, 0 dépendance externe).
"""

import hashlib
import secrets
from typing import Optional


def hash_password(password: str) -> str:
    """
    Génère un hachage sécurisé du mot de passe avec un sel unique de 16 octets.
    Format retourné : <sel_hex>$<hash_hex>
    """
    if not password:
        password = "alternia2026"
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, stored_hash: Optional[str]) -> bool:
    """
    Vérifie si le mot de passe en clair correspond au hash stocké.
    Compatible avec les hashs PBKDF2 avec sel et les hashs SHA256 simples.
    """
    if not stored_hash or not plain_password:
        return False

    if "$" not in stored_hash:
        # Fallback pour hash sha256 simple
        computed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(computed, stored_hash)

    try:
        salt, key_hex = stored_hash.split("$", 1)
        new_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return secrets.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False
