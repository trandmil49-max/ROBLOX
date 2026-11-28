"""Telegram poller. Started by GitHub Actions (poll.yml, woken every couple of minutes by cron-job.org).
It listens for ~100 seconds, so replies are near-instant while the job is alive."""
import os, sys, time, base64, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'engine'))
import tg, messages as T
import story as S

ALLOWED = os.environ.get('ALLOWED_CHAT_ID', '').strip()
POLL_SECONDS = int(os.environ.get('POLL_SECONDS', '100'))
MAX_STORY_CHARS = 60000
AUDIO_EXT = ('.mp3', '.wav', '.m4a', '.ogg', '.oga', '.aac', '.flac', '.opus')

def media_of(msg):
    """Return ('audio', file_id, size) or ('story', text) or None for a message."""
    if not msg: return None
    if 'audio' in msg: a = msg['audio']; return ('audio', a['file_id'], a.get('file_size', 0))
    if 'voice' in msg: a = msg['voice']; return ('audio', a['file_id'], a.get('file_size', 0))
    if 'document' in msg:
        d = msg['document']; name = (d.get('file_name') or '').lower(); mt = d.get('mime_type') or ''
        if name.endswith(AUDIO_EXT) or mt.startswith('audio/'): return ('audio', d['file_id'], d.get('file_size', 0))
        if name.endswith(('.txt', '.md', '.story', '.json')) or mt.startswith('text/'): return ('story_doc', d['file_id'], d.get('file_size', 0))
    if msg.get('text') and not msg['text'].startswith('/') and ('::' in msg['text']): return ('story_text', msg['text'])
    return None

def load_story_text(m):
    if m[0] == 'story_text': return m[1]
    path = f'/tmp/story_{int(time.time()*1000)}.txt'
    if not tg.download(m[1], path): return None
    return open(path, encoding='utf-8', errors='replace').read()

def validate(text):
    st = S.parse_story(text)
    words = sum(len(s['narr'].split()) for s in st['shots'])
    return st, words

def start_render(chat_id, story_text, audio_id, quality='final'):
    if len(story_text) > MAX_STORY_CHARS: tg.send(chat_id, T.TOO_BIG.format(chars=len(story_text), limit=MAX_STORY_CHARS)); return
    st, words = validate(story_text)
    if not st['shots']: tg.send(chat_id, T.BAD_STORY); return
    for line in story_text.splitlines():
        if line.upper().startswith('QUALITY:'): quality = line.split(':', 1)[1].strip().lower()
    if quality not in ('final', 'draft', 'test'): quality = 'final'
    b64 = base64.b64encode(story_text.encode('utf-8')).decode()
    ok = tg.dispatch('render.yml', dict(chat_id=str(chat_id), story_b64=b64, audio_file_id=audio_id, quality=quality, mode='user'))
    if ok: tg.send(chat_id, T.STARTED.format(shots=len(st['shots']), quality={'final': '1080p 60 fps', 'draft': 'taslak', 'test': 'test'}[quality]))
    else: tg.send(chat_id, '⚠️ GitHub işi başlatılamadı. Token izinlerini (Actions: write) kontrol et.')

def handle(msg):
    chat_id = msg['chat']['id']; text = (msg.get('text') or '').strip()
    cmd = text.split()[0].split('@')[0].lower() if text.startswith('/') else ''
    if cmd == '/id': tg.send(chat_id, T.ID_TEXT.format(chat_id=chat_id)); return
    if not ALLOWED: tg.send(chat_id, T.NEED_ID.format(chat_id=chat_id)); return
    if str(chat_id) != ALLOWED: tg.send(chat_id, T.NOT_ALLOWED); return
    if cmd in ('/start', '/help'): tg.send(chat_id, T.HELP); return
    if cmd in ('/test', '/testhd'):
        q = 'test' if cmd == '/test' else 'final'
        if tg.dispatch('render.yml', dict(chat_id=str(chat_id), story_b64='', audio_file_id='', quality=q, mode='demo')): tg.send(chat_id, T.DEMO_STARTED.format(quality='1080p 60 fps' if q == 'final' else 'düşük kalite'))
        else: tg.send(chat_id, '⚠️ GitHub işi başlatılamadı. Token izinlerini kontrol et.')
        return
    if cmd == '/status':
        rows = []
        for st in ('in_progress', 'queued'):
            for r in tg.runs('render.yml', st): rows.append(T.STATUS_ROW.format(name=f"#{r['run_number']}", status='çalışıyor' if st == 'in_progress' else 'sırada'))
        tg.send(chat_id, '\n'.join(rows) if rows else T.NO_JOBS); return
    if cmd == '/cancel':
        n = 0
        for st in ('in_progress', 'queued'):
            for r in tg.runs('render.yml', st): n += 1 if tg.cancel(r['id']) else 0
        tg.send(chat_id, T.CANCELLED.format(n=n) if n else T.NO_JOBS); return
    m = media_of(msg); rep = media_of(msg.get('reply_to_message'))
    if not m: return
    audio = story = None
    for x in (m, rep):
        if x and x[0] == 'audio': audio = x
        if x and x[0] in ('story_doc', 'story_text'): story = x
    if audio and story:
        if audio[2] and audio[2] > 20 * 1024 * 1024: tg.send(chat_id, T.AUDIO_TOO_BIG); return
        txt = load_story_text(story)
        if not txt: tg.send(chat_id, T.BAD_STORY); return
        start_render(chat_id, txt, audio[1])
    elif m[0] == 'audio': tg.send(chat_id, T.GOT_AUDIO)
    elif m[0] in ('story_doc', 'story_text'):
        txt = load_story_text(m)
        if txt:
            st, words = validate(txt)
            tg.send(chat_id, T.GOT_STORY.format(shots=len(st['shots']), words=words) if st['shots'] else T.BAD_STORY)

def main():
    if not tg.TOKEN: print('TELEGRAM_BOT_TOKEN is missing'); sys.exit(1)
    # a hint file lets the job end quickly if nothing happens
    end = time.time() + POLL_SECONDS; offset = None; handled = 0
    while time.time() < end:
        ups = tg.get_updates(offset, timeout=min(25, max(1, int(end - time.time()))))
        for u in ups:
            offset = u['update_id'] + 1
            msg = u.get('message')
            if not msg: continue
            try: handle(msg); handled += 1
            except Exception as e: print('handler error', repr(e))
        if ups: tg.get_updates(offset, timeout=0)   # acknowledge
    print('poll finished, handled', handled)

if __name__ == '__main__': main()
