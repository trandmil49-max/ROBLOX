"""Final step of a render: sends the video (or a download link) to Telegram."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tg, messages as T

chat = os.environ['CHAT_ID']; out = sys.argv[1]; link = os.environ.get('RELEASE_LINK', '')
info = json.load(open(os.path.join(out, 'info.json')))
caption = T.DONE_VIDEO.format(duration=int(info['duration']), size=info['size_mb'], link=link)
ok = False
if info['preview_mb'] <= 49:
    ok = tg.send_video(chat, info['preview'], caption=caption, duration=info['duration'], width=720 if info['preview'] != info['final'] else None, height=1280 if info['preview'] != info['final'] else None)
if not ok: tg.send(chat, T.DONE_LINK.format(duration=int(info['duration']), size=info['size_mb'], link=link))
