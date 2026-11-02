"""
Telegram storage — direct upload/download, no local media.
Limits: 50 MB upload, 20 MB download (Bot API).
"""
import requests
from decouple import config

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID', default='')
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def upload_to_telegram(file_obj, filename=None):
    """Upload file to Telegram. Returns dict with file_id/message_id, or None."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            f"[telegram] MISSING CONFIG — "
            f"TOKEN={'set' if TELEGRAM_BOT_TOKEN else 'EMPTY'}, "
            f"CHAT_ID={'set' if TELEGRAM_CHAT_ID else 'EMPTY'}"
        )
        return None

    if not filename:
        filename = getattr(file_obj, 'name', 'file')

    try:
        file_obj.seek(0)
    except Exception:
        pass

    try:
        files = {'document': (filename, file_obj)}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        r = requests.post(f"{TELEGRAM_API}/sendDocument", data=data, files=files, timeout=60)
        print(f"[telegram] HTTP status: {r.status_code}")
        print(f"[telegram] response: {r.text[:500]}")
        res = r.json()

        if not res.get('ok'):
            print("Telegram upload failed:", res)
            return None

        doc = res['result'].get('document')
        if not doc:
            return None

        return {
            'file_id': doc['file_id'],
            'file_name': doc.get('file_name', filename),
            'file_size': doc.get('file_size', 0),
            'message_id': res['result']['message_id'],
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Telegram upload exception:", e)
        return None


def get_telegram_file_url(file_id):
    """Resolve a file_id to a download URL."""
    if not TELEGRAM_BOT_TOKEN:
        return None
    try:
        r = requests.get(f"{TELEGRAM_API}/getFile", params={'file_id': file_id}, timeout=30)
        res = r.json()
        if not res.get('ok'):
            return None
        path = res['result'].get('file_path')
        if not path:
            return None
        return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{path}"
    except Exception as e:
        print("Telegram getFile exception:", e)
        return None


def delete_telegram_message(message_id):
    """Delete the Telegram message (and its attached file)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not message_id:
        return False
    try:
        r = requests.post(
            f"{TELEGRAM_API}/deleteMessage",
            data={'chat_id': TELEGRAM_CHAT_ID, 'message_id': message_id},
            timeout=30,
        )
        return r.json().get('ok', False)
    except Exception as e:
        print("Telegram delete exception:", e)
        return False