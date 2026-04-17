import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import generate_unique_username
from app.database.model import User
from app.services.admin_alerts_service import maybe_notify_admins_new_user

_SOLANA_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_SOLANA_B58_INDEX = {c: i for i, c in enumerate(_SOLANA_B58_ALPHABET)}
_SOLANA_CHALLENGE_TTL_MINUTES = 10

PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")


def stable_base_url(request: Request) -> str:
    """Prefer PUBLIC_BASE_URL to avoid localhost/0.0.0.0 links; fallback to request base_url."""
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    return str(request.base_url).rstrip("/")


def base58_decode(value: str) -> bytes:
    """
    Decode a base58 string into raw bytes.

    Solana public keys are base58-encoded 32-byte values.
    """
    if not value or not isinstance(value, str):
        raise ValueError("invalid_base58")

    raw_value = value.strip()
    if not raw_value:
        raise ValueError("invalid_base58")

    num = 0
    for ch in raw_value:
        if ch not in _SOLANA_B58_INDEX:
            raise ValueError("invalid_base58")
        num = (num * 58) + _SOLANA_B58_INDEX[ch]

    decoded = num.to_bytes((num.bit_length() + 7) // 8, "big") if num > 0 else b""

    leading_zeroes = 0
    for ch in raw_value:
        if ch == "1":
            leading_zeroes += 1
        else:
            break

    return (b"\x00" * leading_zeroes) + decoded


def validate_solana_public_key(public_key: str) -> str:
    """
    Validate and normalize a Solana public key string.
    Returns the stripped key if valid.
    """
    pk = (public_key or "").strip()
    try:
        raw = base58_decode(pk)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalidWalletAddress")

    if len(raw) != 32:
        raise HTTPException(status_code=400, detail="invalidWalletAddress")

    return pk


def public_key_bytes(public_key: str) -> bytes:
    """
    Convert a validated Solana public key string to 32 raw bytes.
    """
    pk = validate_solana_public_key(public_key)
    try:
        raw = base58_decode(pk)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalidWalletAddress")

    if len(raw) != 32:
        raise HTTPException(status_code=400, detail="invalidWalletAddress")

    return raw


def signature_bytes(signature: str, encoding: str | None = "base64") -> bytes:
    """
    Decode a wallet signature payload into raw bytes.
    Currently supports base64 only.
    """
    enc = (encoding or "base64").strip().lower()
    sig = (signature or "").strip()

    if not sig:
        raise HTTPException(status_code=400, detail="missingWalletSignature")

    try:
        if enc == "base64":
            raw = base64.b64decode(sig, validate=True)
        else:
            raise HTTPException(status_code=400, detail="unsupportedSignatureEncoding")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="invalidWalletSignature")

    if not raw:
        raise HTTPException(status_code=400, detail="invalidWalletSignature")

    return raw


def challenge_hash(message: str) -> str:
    """
    Hash the exact wallet challenge message as UTF-8.
    """
    return hashlib.sha256((message or "").encode("utf-8")).hexdigest()


def build_solana_challenge_message(
    request: Request,
    public_key: str,
    nonce: str,
    expires_at: datetime,
) -> str:
    """
    Build the exact message that the wallet must sign.
    """
    base_url = stable_base_url(request)
    issued_at = datetime.now(timezone.utc).isoformat()
    expires_iso = expires_at.astimezone(timezone.utc).isoformat()

    return (
        "Sign in to SAP with your Solana wallet.\n\n"
        f"URI: {base_url}\n"
        f"Public Key: {public_key}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at}\n"
        f"Expiration Time: {expires_iso}"
    )


def build_solana_challenge_expires_at() -> datetime:
    """
    Return the default expiry timestamp for a wallet challenge.
    """
    return datetime.now(timezone.utc) + timedelta(minutes=_SOLANA_CHALLENGE_TTL_MINUTES)


def verify_solana_signature(
    public_key: str,
    message: str,
    signature: str,
    encoding: str | None = "base64",
) -> None:
    """
    Verify an Ed25519 signature produced by a Solana wallet.

    Raises HTTPException on failure, returns None on success.
    """
    pk_bytes = public_key_bytes(public_key)
    sig_bytes = signature_bytes(signature, encoding)

    if len(sig_bytes) != 64:
        raise HTTPException(status_code=400, detail="invalidWalletSignature")

    try:
        verifier = Ed25519PublicKey.from_public_bytes(pk_bytes)
        verifier.verify(sig_bytes, (message or "").encode("utf-8"))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="walletSignatureVerificationFailed")


def find_or_create_solana_user(db: Session, public_key: str) -> User:
    """
    Find an existing wallet user or create a new pending user for this Solana public key.
    """
    normalized_public_key = validate_solana_public_key(public_key)

    user = db.query(User).filter(User.wallet_address == normalized_public_key).first()
    if user:
        if not getattr(user, "wallet_auth_chain", None):
            user.wallet_auth_chain = "solana"
            db.commit()
            db.refresh(user)
        return user

    suffix = int(hashlib.sha256(normalized_public_key.encode("utf-8")).hexdigest(), 16) % 1_000_000
    username = f"solana_user{suffix}"

    if db.query(User).filter(User.username == username).first():
        username = generate_unique_username(db, User, preferred=username)

    display_name = f"{normalized_public_key[:6]}...{normalized_public_key[-6:]}"

    user = User(
        username=username,
        wallet_address=normalized_public_key,
        wallet_auth_chain="solana",
        display_name=display_name,
        is_confirmed=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    maybe_notify_admins_new_user(db, user, source="solana")
    return user