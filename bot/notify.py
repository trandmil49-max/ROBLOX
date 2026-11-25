"""Kullanim: python3 bot/notify.py "mesaj"   (CHAT_ID ve TELEGRAM_BOT_TOKEN ortam degiskenleri gerekir)"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import tg  # noqa: E402

if __name__ == "__main__":
    chat = os.environ.get("CHAT_ID", "").strip()
    text = " ".join(sys.argv[1:]).strip()
    if not chat or not text:
        print("CHAT_ID veya mesaj yok, atlandi.")
        sys.exit(0)
    try:
        tg.send_message(chat, text)
    except Exception as e:  # bildirim hatasi isi bozmasin
        print("Bildirim gonderilemedi:", e)
