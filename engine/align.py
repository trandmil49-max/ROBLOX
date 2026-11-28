"""Word timing: aligns the narration text to the voice recording (speech recognition + text alignment), with a
silence-based fallback. The subtitles always use the *script* words, never the recognised words."""
import os, re, subprocess, json, difflib, math, wave
from story import fold

LANG_CODES = {'tr': 'tr', 'en': 'en', 'es': 'es', 'fr': 'fr', 'ar': 'ar'}

def to_wav(src, dst, sr=16000):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', str(sr), '-vn', dst], check=True)
    return dst

def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    return float(out)

def speech_region(wav_path, thresh_db=-38):
    """Return (start, end) of speech using ffmpeg silencedetect."""
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', wav_path, '-af', f'silencedetect=noise={thresh_db}dB:d=0.25', '-f', 'null', '-'], capture_output=True, text=True).stderr
    total = duration(wav_path)
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    s = 0.0; e = total
    if ends and starts and starts[0] < 0.05: s = ends[0]
    if starts and (not ends or starts[-1] > (ends[-1] if ends else 0)): e = starts[-1]
    return max(0.0, s - 0.03), max(s + 0.5, e)

def fallback_times(tokens, wav_path):
    """Spread words over the speech region proportionally to their length (plus pauses after punctuation)."""
    s, e = speech_region(wav_path)
    w = [max(2, len(t)) + (4 if re.search(r'[.,;:!?…]$', t) else 0) for t in tokens]
    tot = sum(w) or 1; t = s; out = []
    for x in w:
        d = (e - s) * x / tot; out.append((t, t + d * 0.9)); t += d
    return out

def asr_words(wav_path, lang, model_size=None):
    from faster_whisper import WhisperModel
    size = model_size or os.environ.get('WHISPER_MODEL', 'small')
    model = WhisperModel(size, device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 2)
    segs, _ = model.transcribe(wav_path, language=LANG_CODES.get(lang), word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False)
    out = []
    for sg in segs:
        for w in (sg.words or []): out.append((fold(w.word), float(w.start), float(w.end)))
    return [o for o in out if o[0]]

def align_to_script(script_tokens, asr):
    """script_tokens: raw words. asr: [(norm, start, end)]. Returns [(start,end)] per script token (None where unknown)."""
    a = [fold(t) for t in script_tokens]; b = [x[0] for x in asr]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    res = [None] * len(a)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1): res[i1 + k] = (asr[j1 + k][1], asr[j1 + k][2])
        elif tag == 'replace' and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1): res[i1 + k] = (asr[j1 + k][1], asr[j1 + k][2])
        elif tag == 'replace':
            # spread script words across the span of the recognised words
            s, e = asr[j1][1], asr[j2 - 1][2]; n = i2 - i1
            for k in range(n): res[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 0.9) / n)
    return res

def fill_gaps(res, tokens, lo, hi):
    n = len(res); i = 0
    while i < n:
        if res[i] is None:
            j = i
            while j < n and res[j] is None: j += 1
            left = res[i - 1][1] if i > 0 else lo
            right = res[j][0] if j < n else hi
            right = max(right, left + 0.12 * (j - i))
            w = [max(2, len(tokens[k])) for k in range(i, j)]; tot = sum(w); t = left
            for k, x in zip(range(i, j), w):
                d = (right - left) * x / tot; res[k] = (t, t + d * 0.9); t += d
            i = j
        else: i += 1
    # monotonic
    prev = 0.0
    for k in range(n):
        s, e = res[k]; s = max(s, prev); e = max(e, s + 0.05); res[k] = (s, e); prev = s + 0.04
    return res

def word_times(audio_path, tokens, lang, workdir):
    os.makedirs(workdir, exist_ok=True)
    wav = to_wav(audio_path, os.path.join(workdir, 'voice16k.wav'))
    total = duration(wav); method = 'asr'
    try:
        asr = asr_words(wav, lang)
        if len(asr) < max(3, len(tokens) * 0.3): raise RuntimeError('too few recognised words')
        res = align_to_script(tokens, asr)
        matched = sum(1 for r in res if r is not None)
        s, e = speech_region(wav)
        res = fill_gaps(res, tokens, asr[0][1], min(total, asr[-1][2] + 0.3))
        info = f'asr matched {matched}/{len(tokens)} words'
    except Exception as ex:
        method = 'fallback'; info = f'fallback timing ({ex})'
        res = fallback_times(tokens, wav)
    return res, total, dict(method=method, info=info)
