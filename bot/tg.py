"""Telegram yardimci fonksiyonlari (sadece standart kutuphane)."""
import json
import os
import urllib.error
import urllib.request

BASE = "https://api.telegram.org"


def _token():
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def api(method, params=None, timeout=60):
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(
        f"{BASE}/bot{_token()}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode() or "{}")
        except Exception:
            body = {"ok": False, "description": f"HTTP {e.code}"}
    if not body.get("ok"):
        raise RuntimeError(f"Telegram {method} hatasi: {body.get('description')}")
    return body["result"]


def send_message(chat_id, text):
    return api(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
    )


def download_file(file_id, dest):
    info = api("getFile", {"file_id": file_id})
    path = info.get("file_path")
    if not path:
        raise RuntimeError("Telegram dosya yolunu vermedi (dosya 20 MB'tan buyuk olabilir).")
    url = f"{BASE}/file/bot{_token()}/{path}"
    urllib.request.urlretrieve(url, dest)
    return dest
