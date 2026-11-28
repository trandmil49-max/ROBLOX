"""Minimal Telegram + GitHub API helpers (requests only)."""
import os, json, time, requests

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
API = f'https://api.telegram.org/bot{TOKEN}'
FILE_API = f'https://api.telegram.org/file/bot{TOKEN}'
GH = 'https://api.github.com'
REPO = os.environ.get('GITHUB_REPOSITORY', '')
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')

def token_note():
    """Small footer reminding the owner when the GitHub token expires (secret TOKEN_EXPIRES = YYYY-MM-DD)."""
    import datetime
    raw = os.environ.get('TOKEN_EXPIRES', '').strip()
    if not raw: return '\n\n<i>🔑 Token bitiş tarihi kayıtlı değil. GitHub Secrets içine TOKEN_EXPIRES (YYYY-AA-GG) ekle.</i>'
    try: d = datetime.date.fromisoformat(raw)
    except ValueError: return '\n\n<i>🔑 TOKEN_EXPIRES biçimi hatalı (YYYY-AA-GG olmalı).</i>'
    left = (d - datetime.date.today()).days
    if left < 0: return f'\n\n<i>🔴 GitHub token {-left} gün önce bitti! Hemen yeni token al.</i>'
    if left <= 14: return f'\n\n<i>🟠 GitHub token {d.strftime("%d.%m.%Y")} tarihinde bitiyor ({left} gün kaldı). Yeni token al!</i>'
    return f'\n\n<i>🔑 GitHub token bitiş: {d.strftime("%d.%m.%Y")} ({left} gün kaldı)</i>'

def call(method, **params):
    for _ in range(3):
        try:
            r = requests.post(f'{API}/{method}', json=params, timeout=40)
            data = r.json()
            if data.get('ok'): return data['result']
            if data.get('error_code') == 429: time.sleep(data.get('parameters', {}).get('retry_after', 3)); continue
            print('telegram error', method, data); return None
        except Exception as e:
            print('telegram exception', method, e); time.sleep(2)
    return None

def send(chat_id, text, note=True, **kw):
    if note and len(text) < 3800: text = text + token_note()
    return call('sendMessage', chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True, **kw)

def get_updates(offset=None, timeout=25):
    params = dict(timeout=timeout, allowed_updates=['message'])
    if offset is not None: params['offset'] = offset
    try:
        r = requests.post(f'{API}/getUpdates', json=params, timeout=timeout + 15)
        d = r.json()
        return d.get('result', []) if d.get('ok') else []
    except Exception as e:
        print('getUpdates failed', e); return []

def download(file_id, dest):
    info = call('getFile', file_id=file_id)
    if not info: return None
    r = requests.get(f"{FILE_API}/{info['file_path']}", timeout=120); r.raise_for_status()
    with open(dest, 'wb') as f: f.write(r.content)
    return dest

def send_video(chat_id, path, caption='', duration=None, width=None, height=None):
    caption = (caption + token_note())[:1000]
    with open(path, 'rb') as f:
        data = dict(chat_id=chat_id, caption=caption, parse_mode='HTML', supports_streaming='true')
        if duration: data['duration'] = int(duration)
        if width: data['width'] = width
        if height: data['height'] = height
        r = requests.post(f'{API}/sendVideo', data=data, files={'video': f}, timeout=600)
    try: return r.json().get('ok', False)
    except Exception: return False

def gh_headers():
    return {'Authorization': f'Bearer {GH_TOKEN}', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}

def dispatch(workflow, inputs, ref=None):
    ref = ref or os.environ.get('GITHUB_REF_NAME', 'main')
    r = requests.post(f'{GH}/repos/{REPO}/actions/workflows/{workflow}/dispatches', headers=gh_headers(), json=dict(ref=ref, inputs=inputs), timeout=30)
    print('dispatch', workflow, r.status_code, r.text[:200])
    return r.status_code in (200, 201, 204)

def runs(workflow, status=None):
    p = {'per_page': 20}
    if status: p['status'] = status
    r = requests.get(f'{GH}/repos/{REPO}/actions/workflows/{workflow}/runs', headers=gh_headers(), params=p, timeout=30)
    return r.json().get('workflow_runs', []) if r.status_code == 200 else []

def cancel(run_id):
    return requests.post(f'{GH}/repos/{REPO}/actions/runs/{run_id}/cancel', headers=gh_headers(), timeout=30).status_code in (200, 202)

def run_jobs(run_id):
    r = requests.get(f'{GH}/repos/{REPO}/actions/runs/{run_id}/jobs', headers=gh_headers(), params={'per_page': 100}, timeout=30)
    return r.json().get('jobs', []) if r.status_code == 200 else []
