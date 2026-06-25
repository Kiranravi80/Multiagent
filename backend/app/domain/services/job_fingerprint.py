"""
Job Fingerprint Service.

Pure domain logic for generating deterministic dedup fingerprints.
"""

from __future__ import annotations

import hashlib


def generate_fingerprint(title: str, company: str) -> str:
    """
    Generate a deterministic dedup fingerprint from title + company.

    The same job posted on multiple boards will produce the same fingerprint,
    preventing duplicate entries in the database.

    Args:
        title: Job title.
        company: Company name.

    Returns:
        A 32-character hex digest (SHA-256 truncated).
    """
    raw = f"{title.lower().strip()}|{company.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
