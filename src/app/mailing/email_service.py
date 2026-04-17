import os
import json
import threading
from typing import Iterable, Any, Dict
from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape

from dotenv import load_dotenv
load_dotenv()


PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://sap.mobr.ai').rstrip('/')
RESEND_API_KEY = os.environ['RESEND_API_KEY']
SERVICE_MAIL = os.environ.get("SERVICE_MAIL", "team@mobr.ai")
APP_NAME = os.environ.get('APP_NAME', 'SAP')
APP_FULL_NAME = os.environ.get('APP_FULL_NAME', 'Solana Analytics Platform')
APP_TAGLINE = os.environ.get('APP_TAGLINE', 'Solana intelligence, structured.')
APP_LOGO_URL = os.environ.get(
    "APP_LOGO_URL",
    "https://raw.githubusercontent.com/mobr-ai/sap-frontend/refs/heads/main/public/icons/logo.png",
)
APP_UNSUB_URL = os.environ.get('APP_UNSUB_URL', f'{PUBLIC_BASE_URL}/unsubscribe')

HERE = Path(__file__).resolve().parent
resend.api_key = RESEND_API_KEY


def _load_translations():
    candidates = [
        HERE / 'translation.json',
        HERE / 'i18n' / 'sap_emails.json',
        HERE / 'i18n' / 'cap_emails.json',
        Path.cwd() / 'src' / 'sap' / 'mailing' / 'translation.json',
        Path.cwd() / 'translation.json',
    ]
    last_err = None
    for p in candidates:
        try:
            if p.is_file():
                with p.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f'[mailing] Loaded translations from: {p}')
                return data
        except Exception as e:
            last_err = e
    print(f'[mailing] WARNING: could not load translations; last error: {last_err}')
    return {}


TRANSLATIONS = _load_translations()

TEMPLATE_DIRS = [
    str(HERE / 'templates'),
    'templates',
]

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIRS),
    autoescape=select_autoescape(['html', 'xml']),
)


def _lang(code: str | None) -> str:
    code = (code or 'en').lower()
    return 'pt' if code.startswith('pt') else 'en'


def render_template(template_name: str, language: str, **kwargs) -> str:
    lang = _lang(language)
    key = template_name[:-5] if template_name.endswith('.html') else template_name

    base_tr = TRANSLATIONS.get('base_email', {}).get(lang, {}) or {}
    page_tr = TRANSLATIONS.get(key, {}).get(lang, {}) or {}
    merged_tr = {**base_tr, **page_tr}

    template = env.get_template(
        template_name if template_name.endswith('.html') else f'{template_name}.html'
    )
    return template.render(
        translations=merged_tr,
        language='pt-BR' if lang == 'pt' else 'en',
        app_name=APP_NAME,
        app_full_name=APP_FULL_NAME,
        app_tagline=APP_TAGLINE,
        app_logo_url=APP_LOGO_URL,
        unsubscribe_url=APP_UNSUB_URL,
        public_base_url=PUBLIC_BASE_URL,
        support_email=os.environ.get('SUPPORT_EMAIL', SERVICE_MAIL),
        **kwargs,
    )


def send_email(
    to_email: Iterable[str] | str,
    language: str = 'en',
    template_name: str = 'general_notification',
    **kwargs,
):
    html = render_template(template_name, language, **kwargs)
    subject = TRANSLATIONS.get(template_name, {}).get(_lang(language), {}).get('title', 'Notification')

    try:
        response = resend.Emails.send({
            'from': f'{APP_NAME} <{SERVICE_MAIL}>',
            'to': to_email if isinstance(to_email, list) else [to_email],
            'subject': subject,
            'html': html,
        })
        print(f"[mailing] sent '{template_name}' to {to_email}")
        return response
    except Exception as e:
        print(f"[mailing] error sending '{template_name}' to {to_email}: {e}")
        return None


def send_async_email(
    to_email: Iterable[str] | str,
    language: str,
    template_name: str,
    context: Dict[str, Any],
) -> None:
    t = threading.Thread(
        target=send_email,
        kwargs=dict(
            to_email=to_email,
            language=language,
            template_name=template_name,
            **context,
        ),
        daemon=True,
    )
    t.start()
