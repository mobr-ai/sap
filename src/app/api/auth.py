import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.google_oauth import get_userinfo_from_access_token_or_idtoken
from app.core.security import (
    generate_unique_username,
    hash_password,
    make_access_token,
    new_confirmation_token,
    verify_password,
)
from app.core.solana_auth import (
    build_solana_challenge_expires_at,
    build_solana_challenge_message,
    challenge_hash,
    find_or_create_solana_user,
    signature_bytes,
    validate_solana_public_key,
    verify_solana_signature,
)
from app.database.model import User
from app.database.session import get_db
from app.mailing.event_triggers import on_user_access_granted
from app.services.admin_alerts_service import maybe_notify_admins_new_user

try:
    from app.mailing.event_triggers import (
        on_confirmation_resent,
        on_oauth_login,
        on_user_confirmed,
        on_user_registered,
        on_waiting_list_joined,
        on_wallet_login,
    )
except Exception:
    def on_user_registered(*args, **kwargs):
        pass

    def on_waiting_list_joined(*args, **kwargs):
        pass

    def on_confirmation_resent(*args, **kwargs):
        pass

    def on_user_confirmed(*args, **kwargs):
        pass

    def on_oauth_login(*args, **kwargs):
        pass

    def on_wallet_login(*args, **kwargs):
        pass


route_prefix = "/api/v1"
router = APIRouter(prefix=route_prefix, tags=["auth"])

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")


def _stable_base_url(request: Request) -> str:
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL.rstrip("/")
    return str(request.base_url).rstrip("/")


def _make_referral_link(base_url: str, user_id: int | None) -> str:
    if user_id:
        return f"{base_url}/signup?ref=u{user_id}"
    return f"{base_url}/signup"


class SolanaChallengeIn(BaseModel):
    public_key: str
    language: str | None = "en"


class SolanaVerifyIn(BaseModel):
    public_key: str
    message: str
    signature: str
    signature_encoding: str | None = "base64"
    remember_me: bool = True
    language: str | None = "en"


class ResendSetupLinkIn(BaseModel):
    email: EmailStr
    language: str | None = "en"


class WalletClaimEmailIn(BaseModel):
    user_id: int
    wallet_address: str
    email: EmailStr
    ref: str | None = ""
    language: str | None = "en"


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    language: str | None = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class ResendIn(BaseModel):
    email: EmailStr
    language: str | None = "en"


class GoogleIn(BaseModel):
    token: str
    token_type: str | None = None
    remember_me: bool = False
    language: str | None = "en"
    ref: str | None = ""


class CardanoIn(BaseModel):
    address: str
    remember_me: bool = True
    language: str | None = "en"
    ref: str | None = ""


class SetPasswordIn(BaseModel):
    token: str
    password: str
    remember_me: bool = False


def _ensure_waitlist_row(
    db: Session, email: str, ref: str = "", language: str = "en"
) -> bool:
    e = (email or "").strip().lower()
    if not e:
        return False

    exists = db.execute(
        text("SELECT 1 FROM waiting_list WHERE email = :e"),
        {"e": e},
    ).first()
    if exists:
        return False

    db.execute(
        text("INSERT INTO waiting_list (email, ref, language) VALUES (:e, :r, :l)"),
        {"e": e, "r": ref or "", "l": (language or "en").strip().lower()},
    )
    db.commit()
    return True


@router.post("/auth/wallet_claim_email")
def wallet_claim_email(
    data: WalletClaimEmailIn,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.user_id == data.user_id).first()
    if not user:
        raise HTTPException(404, detail="userNotFound")

    if not user.wallet_address or user.wallet_address != data.wallet_address:
        raise HTTPException(400, detail="walletMismatch")

    email_norm = (str(data.email or "").strip().lower()) if data.email else ""
    if not email_norm:
        raise HTTPException(400, detail="invalidEmailFormat")

    existing = db.query(User).filter(User.email == email_norm).first()
    if existing and existing.user_id != user.user_id:
        raise HTTPException(400, detail="userExistsError")

    user.email = email_norm
    db.commit()

    inserted = _ensure_waitlist_row(
        db,
        email=email_norm,
        ref=(data.ref or ""),
        language=(data.language or "en"),
    )

    if inserted:
        try:
            base_url = _stable_base_url(request)
            referral_link = _make_referral_link(base_url, getattr(user, "user_id", None))
            on_waiting_list_joined(
                to=[email_norm],
                language=(data.language or "en"),
                referral_link=referral_link,
            )
        except Exception as mail_err:
            print(f"[WAITLIST] Mail trigger failed for {email_norm}: {mail_err}")

    if not inserted:
        raise HTTPException(418, detail="alreadyOnList")

    return {"status": "waitlisted", "id": user.user_id, "email": user.email}


@router.post("/register")
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    if not data.email or not data.password:
        raise HTTPException(400, detail="registerError")

    email_norm = data.email.strip().lower()

    user = db.query(User).filter(User.email == email_norm).first()
    if user:
        if user.google_id:
            raise HTTPException(400, detail="oauthExistsError")
        raise HTTPException(400, detail="userExistsError")

    token = new_confirmation_token()
    email_local = email_norm.split("@")[0]

    new_user = User(
        email=email_norm,
        username=generate_unique_username(db, User, preferred=email_local),
        password_hash=hash_password(data.password),
        confirmation_token=token,
        is_confirmed=False,
        is_admin=False,
    )
    db.add(new_user)
    db.commit()

    maybe_notify_admins_new_user(db, new_user, source="password")

    base = str(request.base_url).rstrip("/")
    activation_link = f"{base}/{route_prefix}/confirm/{token}"

    on_user_registered(
        to=[email_norm],
        language=(data.language or "en"),
        username=new_user.username or email_local,
        activation_link=activation_link,
    )

    return {"redirect": "/login?confirmed=false"}


@router.get("/confirm/{token}")
def confirm_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.confirmation_token == token).first()
    if not user:
        raise HTTPException(400, detail="confirmationError")

    user.is_confirmed = True
    user.confirmation_token = None
    db.commit()

    on_user_confirmed(to=[user.email] if user.email else [], language="en")
    return RedirectResponse(url="/login?confirmed=true")


@router.post("/auth/resend_setup_link")
def resend_setup_link(
    data: ResendSetupLinkIn,
    request: Request,
    db: Session = Depends(get_db),
):
    email_norm = (str(data.email or "").strip().lower()) if data.email else ""
    if not email_norm:
        raise HTTPException(400, detail="invalidEmailFormat")

    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        raise HTTPException(404, detail="userNotFound")

    if not bool(user.is_confirmed):
        raise HTTPException(403, detail="accessNotGranted")

    if user.google_id:
        raise HTTPException(400, detail="oauthExistsError")

    if user.password_hash:
        raise HTTPException(400, detail="passwordAlreadySet")

    token = new_confirmation_token()
    user.confirmation_token = token
    db.commit()
    db.refresh(user)

    base_url = _stable_base_url(request)
    setup_url = f"{base_url}/login?state=setpass&token={token}"

    on_user_access_granted(
        to=[email_norm],
        language=(data.language or "en"),
        app_url=base_url,
        setup_url=setup_url,
    )

    return {"status": "sent"}


@router.post("/auth/set_password")
def set_password(data: SetPasswordIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.confirmation_token == data.token).first()
    if not user:
        raise HTTPException(400, detail="invalidOrExpiredToken")

    if not user.is_confirmed:
        raise HTTPException(403, detail="accessNotGranted")

    if user.google_id:
        raise HTTPException(400, detail="oauthExistsError")

    pw = (data.password or "").strip()
    if len(pw) < 8:
        raise HTTPException(400, detail="weakPassword")

    user.password_hash = hash_password(pw)
    user.confirmation_token = None
    db.commit()
    db.refresh(user)

    token = make_access_token(str(user.user_id), remember=data.remember_me)
    return {
        "id": user.user_id,
        "username": user.username,
        "wallet_address": user.wallet_address,
        "display_name": user.display_name,
        "email": user.email,
        "avatar": user.avatar,
        "settings": user.settings,
        "is_admin": getattr(user, "is_admin", False),
        "access_token": token,
    }


@router.post("/resend_confirmation")
def resend_confirmation(data: ResendIn, request: Request, db: Session = Depends(get_db)):
    email_norm = (str(data.email or "").strip().lower()) if data.email else ""
    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        raise HTTPException(404, detail="userNotFound")

    if user.is_confirmed:
        raise HTTPException(400, detail="alreadyConfirmed")

    token = new_confirmation_token()
    user.confirmation_token = token
    db.commit()

    on_confirmation_resent(to=[email_norm], language=(data.language or "en"))
    return {"message": "resent"}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    email_norm = (str(data.email or "").strip().lower()) if data.email else ""
    if not email_norm:
        raise HTTPException(401, detail="loginError")

    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        raise HTTPException(401, detail="loginError")

    if not user.is_confirmed:
        raise HTTPException(403, detail="confirmationError")

    if not user.password_hash:
        if user.google_id:
            raise HTTPException(400, detail="oauthExistsError")
        raise HTTPException(403, detail="passwordNotSet")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(401, detail="loginError")

    token = make_access_token(str(user.user_id), remember=data.remember_me)

    resp = {
        "id": user.user_id,
        "username": user.username,
        "wallet_address": user.wallet_address,
        "display_name": user.display_name,
        "email": user.email,
        "avatar": user.avatar,
        "settings": user.settings,
        "is_admin": getattr(user, "is_admin", False),
        "access_token": token,
    }

    if user.google_id:
        resp["notice"] = "googleLinked"

    return resp


@router.post("/auth/google")
def auth_google(data: GoogleIn, request: Request, db: Session = Depends(get_db)):
    try:
        info = get_userinfo_from_access_token_or_idtoken(
            data.token, getattr(data, "token_type", None)
        )

        google_id = info["sub"]
        email = (info.get("email") or "").strip().lower()
        display_name = info.get("name") or ""
        avatar = info.get("picture", "")

        if not email:
            raise HTTPException(400, detail="missingGoogleEmail")

        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            user = db.query(User).filter(User.email == email).first()

            if user:
                if user.google_id and user.google_id != google_id:
                    raise HTTPException(400, detail="oauthExistsError")

                user.google_id = google_id

                if display_name and not user.display_name:
                    user.display_name = display_name
                if avatar and not user.avatar:
                    user.avatar = avatar

                if not user.username:
                    user.username = generate_unique_username(
                        db, User, preferred=(email.split("@")[0] or display_name)
                    )

                db.commit()
            else:
                username = generate_unique_username(
                    db, User, preferred=(email.split("@")[0] or display_name)
                )
                user = User(
                    google_id=google_id,
                    email=email,
                    username=username,
                    display_name=display_name,
                    avatar=avatar,
                    is_confirmed=False,
                    is_admin=False,
                )
                db.add(user)
                db.commit()
                maybe_notify_admins_new_user(db, user, source="google")

        else:
            if email and not user.email:
                user.email = email
            if display_name and not user.display_name:
                user.display_name = display_name
            if avatar and not user.avatar:
                user.avatar = avatar
            db.commit()

        if not bool(user.is_confirmed):
            inserted = _ensure_waitlist_row(
                db,
                email=email,
                ref=(data.ref or ""),
                language=(data.language or "en"),
            )

            if inserted:
                try:
                    base_url = _stable_base_url(request)
                    referral_link = _make_referral_link(base_url, getattr(user, "user_id", None))
                    on_waiting_list_joined(
                        to=[email],
                        language=(data.language or "en"),
                        referral_link=referral_link,
                    )
                except Exception as mail_err:
                    print(f"[WAITLIST] Mail trigger failed for {email}: {mail_err}")

            return {"status": "pending_confirmation", "id": user.user_id, "email": user.email}

        token = make_access_token(str(user.user_id), remember=data.remember_me)
        on_oauth_login(to=[email], language=(data.language or "en"), provider="Google")

        return {
            "id": user.user_id,
            "username": user.username,
            "wallet_address": user.wallet_address,
            "display_name": user.display_name,
            "email": user.email,
            "avatar": user.avatar,
            "settings": user.settings,
            "is_admin": getattr(user, "is_admin", False),
            "access_token": token,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))


@router.post("/auth/solana/challenge")
def solana_challenge(
    data: SolanaChallengeIn,
    request: Request,
    db: Session = Depends(get_db),
):
    public_key = validate_solana_public_key(data.public_key)
    user = find_or_create_solana_user(db, public_key)

    nonce = new_confirmation_token()
    expires_at = build_solana_challenge_expires_at()
    message = build_solana_challenge_message(request, public_key, nonce, expires_at)

    user.wallet_challenge_hash = challenge_hash(message)
    user.wallet_challenge_expires_at = expires_at
    user.wallet_auth_chain = "solana"
    db.commit()
    db.refresh(user)

    return {
        "public_key": public_key,
        "message": message,
        "expires_at": expires_at.isoformat(),
    }


@router.post("/auth/solana/verify")
def solana_verify(
    data: SolanaVerifyIn,
    db: Session = Depends(get_db),
):
    public_key = validate_solana_public_key(data.public_key)

    user = db.query(User).filter(User.wallet_address == public_key).first()
    if not user:
        raise HTTPException(404, detail="userNotFound")

    wallet_chain = getattr(user, "wallet_auth_chain", None)
    if wallet_chain not in (None, "", "solana"):
        raise HTTPException(400, detail="walletChainMismatch")

    if not user.wallet_challenge_hash or not user.wallet_challenge_expires_at:
        raise HTTPException(400, detail="missingWalletChallenge")

    now = datetime.now(timezone.utc)
    expires_at = user.wallet_challenge_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        user.wallet_challenge_hash = None
        user.wallet_challenge_expires_at = None
        db.commit()
        raise HTTPException(400, detail="walletChallengeExpired")

    incoming_message = data.message or ""
    incoming_hash = challenge_hash(incoming_message)
    if incoming_hash != user.wallet_challenge_hash:
        raise HTTPException(400, detail="walletChallengeMismatch")

    sig_bytes = signature_bytes(data.signature, data.signature_encoding)
    if len(sig_bytes) != 64:
        raise HTTPException(400, detail="invalidWalletSignature")

    verify_solana_signature(
        public_key=public_key,
        message=incoming_message,
        signature=data.signature,
        encoding=data.signature_encoding or "base64",
    )

    user.wallet_challenge_hash = None
    user.wallet_challenge_expires_at = None
    user.wallet_last_signed_at = now
    user.wallet_auth_chain = "solana"
    db.commit()
    db.refresh(user)

    if not bool(user.is_confirmed):
        return {
            "status": "pending_confirmation",
            "id": user.user_id,
            "wallet_address": user.wallet_address,
        }

    token = make_access_token(str(user.user_id), remember=data.remember_me)

    if user.email:
        try:
            on_wallet_login(
                to=[user.email],
                language=(data.language or "en"),
                wallet_address=public_key,
            )
        except Exception:
            pass

    return {
        "id": user.user_id,
        "username": user.username,
        "wallet_address": user.wallet_address,
        "display_name": user.display_name,
        "email": user.email,
        "avatar": user.avatar,
        "settings": user.settings,
        "is_admin": getattr(user, "is_admin", False),
        "access_token": token,
    }