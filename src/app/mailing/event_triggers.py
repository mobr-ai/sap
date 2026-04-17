"""
Mailing triggers for SAP.

Thin wrappers around send_async_email so API/business code stays tidy.
"""

from __future__ import annotations

import os
from typing import Iterable, Mapping, Any

from .email_service import send_async_email


def _lang_or_default(lang: str | None) -> str:
    if not lang:
        return 'en'
    lang = lang.lower()
    if lang.startswith('pt'):
        return 'pt'
    return 'en'


def _public_base_url() -> str:
    return os.getenv('PUBLIC_BASE_URL', 'https://sap.mobr.ai').rstrip('/')


def _app_url() -> str:
    return f'{_public_base_url()}'


def _send(
    template: str,
    to: Iterable[str] | str,
    language: str | None,
    ctx: Mapping[str, Any],
    template_type: str | None = None,
) -> None:
    payload = dict(ctx)
    if template_type:
        payload['template_type'] = template_type

    send_async_email(
        to_email=to,
        language=_lang_or_default(language),
        template_name=template,
        context=payload,
    )


def on_waiting_list_joined(
    to: Iterable[str] | str,
    language: str | None,
    referral_link: str,
    app_url: str | None = None,
) -> None:
    _send(
        template='waiting_list_confirmation',
        to=to,
        language=language,
        ctx={
            'referral_link': referral_link,
            'app_url': app_url or _app_url(),
        },
    )


def on_user_registered(
    to: Iterable[str] | str,
    language: str | None,
    username: str,
    activation_link: str,
) -> None:
    _send(
        template='user_registration',
        to=to,
        language=language,
        ctx={'username': username, 'activation_link': activation_link},
    )


def on_confirmation_resent(
    to: Iterable[str] | str,
    language: str | None = 'en',
) -> None:
    _send('user_confirmation_resent', to, language, ctx={})


def on_user_confirmed(
    to: Iterable[str] | str,
    language: str | None = 'en',
) -> None:
    _send('user_confirmed', to, language, ctx={})


def on_oauth_login(
    to: Iterable[str] | str,
    language: str | None = 'en',
    provider: str = 'Google',
) -> None:
    _send('oauth_login', to, language, ctx={'provider': provider}, template_type='auth')


def on_wallet_login(
    to: Iterable[str] | str,
    language: str | None = 'en',
    wallet_address: str = '',
) -> None:
    _send('wallet_login', to, language, ctx={'wallet_address': wallet_address}, template_type='security')


def on_admin_user_created(
    to: Iterable[str] | str,
    language: str | None = 'en',
    new_user_email: str | None = '',
    new_user_username: str | None = '',
    source: str | None = 'password',
) -> None:
    _send(
        template='admin_user_created',
        to=to,
        language=language,
        ctx={
            'new_user_email': new_user_email or '',
            'new_user_username': new_user_username or '',
            'source': source or 'password',
            'app_url': _app_url(),
        },
        template_type='admin',
    )


def on_admin_waitlist_created(
    to: Iterable[str] | str,
    language: str | None = 'en',
    waitlist_email: str | None = '',
    waitlist_ref: str | None = '',
    source: str | None = 'waitlist',
) -> None:
    _send(
        template='admin_waitlist_created',
        to=to,
        language=language,
        ctx={
            'waitlist_email': waitlist_email or '',
            'waitlist_ref': waitlist_ref or '',
            'source': source or 'waitlist',
            'app_url': _app_url(),
        },
        template_type='admin',
    )


def on_user_email_verified(
    to: Iterable[str] | str,
    language: str | None = 'en',
    app_url: str | None = None,
) -> None:
    _send(
        template='user_email_verified',
        to=to,
        language=language,
        ctx={'app_url': app_url or _app_url()},
    )


def on_user_access_granted(
    to: Iterable[str] | str,
    language: str | None = 'en',
    app_url: str | None = None,
    setup_url: str | None = None,
) -> None:
    _send(
        template='user_access_granted',
        to=to,
        language=language,
        ctx={
            'app_url': app_url or _app_url(),
            'setup_url': (setup_url or '').strip() or None,
        },
    )


def on_waitlist_promoted(
    to: Iterable[str] | str,
    language: str | None = 'en',
    app_url: str | None = None,
    setup_url: str | None = None,
) -> None:
    _send(
        template='waitlist_promoted',
        to=to,
        language=language,
        ctx={
            'app_url': app_url or _app_url(),
            'setup_url': (setup_url or '').strip() or None,
        },
    )


def on_admin_user_confirmed(
    *,
    to: list[str],
    language: str,
    confirmed_user_email: str = '',
    confirmed_user_username: str = '',
    confirmed_user_id: int | None = None,
    source: str = 'admin',
    **_ignored,
) -> None:
    _send(
        template='admin_user_confirmed',
        to=to,
        language=language,
        ctx={
            'confirmed_user_email': confirmed_user_email,
            'confirmed_user_username': confirmed_user_username,
            'confirmed_user_id': confirmed_user_id,
            'source': source,
            'app_url': _app_url(),
        },
        template_type='admin',
    )


def on_user_access_revoked(
    to: Iterable[str] | str,
    language: str | None = 'en',
    support_email: str | None = '',
    app_url: str | None = None,
) -> None:
    _send(
        template='user_access_revoked',
        to=to,
        language=language,
        ctx={
            'support_email': support_email or '',
            'app_url': app_url or _app_url(),
        },
        template_type='security',
    )
