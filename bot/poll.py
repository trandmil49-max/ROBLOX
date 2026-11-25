"""Her 5 dakikada bir calisir: Telegram'daki yeni mesajlara bakar, ses + senaryo geldiyse render'i baslatir."""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import tg  # noqa: E402

AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".oga", ".opus", ".aac", ".flac")
MAX_BYTES = 20 * 1024 * 1024  # Telegram botlari en fazla 20 MB indirebilir
MAX_SCRIPT = 60000

HELP = (
    "Nasil kullanilir:\n"
    "1) Once senaryo METNINI yaz/yapistir (birden fazla mesaj olabilir).\n"
    "2) Sonra seslendirdigin MP3 dosyasini gonder (en fazla 20 MB, MP3 olsun).\n"
    "3) Bot 5-10 dk icinde 'Render basladi' der, video bitince indirme linkini yollar.\n\n"
    "Komutlar:\n"
    "/test  - 25 saniyelik deneme videosu uretir\n"
    "/sil   - hazir videolarin linklerini hemen siler\n"
    "/yardim - bu mesaj"
)


def audio_of(m):
    for key in ("audio", "voice"):
        if key in m:
            return m[key]
    d = m.get("document")
    if d and (
        (d.get("mime_type") or "").startswith("audio/")
        or (d.get("file_name") or "").lower().endswith(AUDIO_EXT)
    ):
        return d
    return None


def run(api, send, dispatch, delete_all, allowed):
    updates = api("getUpdates", {"timeout": 0, "limit": 100, "allowed_updates": ["message"]})
    if not updates:
        return
    pending = []  # (update_id, metin)
    confirm = None  # bu id'ye kadar her sey islendi

    for u in updates:
        uid = u["update_id"]
        m = u.get("message")
        if not m:
            if not pending:
                confirm = uid
            continue
        sender = str(m.get("from", {}).get("id", ""))
        chat_id = m["chat"]["id"]
        text = (m.get("text") or "").strip()

        # yetkisiz kisi
        if not allowed or sender != allowed:
            if not pending:
                if text.startswith("/start"):
                    if not allowed:
                        send(chat_id, f"Merhaba! Senin Telegram ID'n: {sender}\n"
                                      "Bu sayiyi GitHub'da ALLOWED_USER_ID adli secret olarak kaydet.")
                    else:
                        send(chat_id, "Bu bot ozeldir.")
                confirm = uid
            continue

        a = audio_of(m)
        if a:
            script = "\n".join(t for _, t in pending).strip() or (m.get("caption") or "").strip()
            pending = []
            confirm = uid
            if not script:
                send(chat_id, "Senaryo metnini bulamadim. Once metni, sonra MP3'u gonder.")
                continue
            if len(script) > MAX_SCRIPT:
                send(chat_id, "Senaryo cok uzun.")
                continue
            if a.get("file_size", 0) > MAX_BYTES:
                send(chat_id, "Ses dosyasi 20 MB'tan buyuk. Lutfen MP3 olarak (kucuk boyutta) gonder.")
                continue
            try:
                dispatch({"audio_file_id": a["file_id"], "script": script, "chat_id": str(chat_id)})
                send(chat_id, "Render basladi. Bitince indirme linkini gonderecegim.")
            except Exception as e:
                send(chat_id, f"Render baslatilamadi: {e}")
            continue

        if text.startswith("/"):
            if pending:
                continue  # senaryo beklerken komutlari erteliyoruz
            cmd = text.split()[0].split("@")[0].lower()
            confirm = uid
            if cmd in ("/start", "/yardim", "/help"):
                send(chat_id, "Hazirim.\n\n" + HELP)
            elif cmd == "/test":
                try:
                    dispatch({"audio_file_id": "TEST", "script": "Bu bir test videosudur.", "chat_id": str(chat_id)})
                    send(chat_id, "Test render basladi (yaklasik 25 saniyelik demo).")
                except Exception as e:
                    send(chat_id, f"Test baslatilamadi: {e}")
            elif cmd == "/sil":
                try:
                    delete_all()
                    send(chat_id, "Hazir videolarin linkleri silindi.")
                except Exception as e:
                    send(chat_id, f"Silinemedi: {e}")
            else:
                send(chat_id, "Bilinmeyen komut. /yardim yaz.")
            continue

        if text:
            pending.append((uid, text))
        elif not pending:
            confirm = uid  # fotograf vb. - yoksay

    if confirm is not None:
        api("getUpdates", {"offset": confirm + 1, "limit": 1, "timeout": 0})


def gh_dispatch(inputs):
    repo = os.environ["GITHUB_REPOSITORY"]
    ref = os.environ.get("GITHUB_REF_NAME") or "main"
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/workflows/render.yml/dispatches",
        data=json.dumps({"ref": ref, "inputs": inputs}).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "video-bot",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub {e.code}: {e.read().decode()[:200]}")


def delete_all():
    subprocess.run(["bash", os.path.join(os.path.dirname(__file__), "cleanup.sh"), "all"], check=True)


def main():
    if not os.environ.get("TELEGRAM_BOT_TOKEN", "").strip():
        print("TELEGRAM_BOT_TOKEN secret'i henuz eklenmemis; atlandi.")
        return
    allowed = os.environ.get("ALLOWED_USER_ID", "").strip()
    run(tg.api, tg.send_message, gh_dispatch, delete_all, allowed)


if __name__ == "__main__":
    main()
