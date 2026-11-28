"""Runs in parallel with a render and sends percentage messages (about every 10%) to the owner."""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tg, messages as T

CHAT = os.environ['CHAT_ID']; RUN_ID = os.environ['RUN_ID']; CHUNKS = int(os.environ.get('CHUNKS', '5'))
W_PLAN, W_RENDER, W_ASM = 6, 84, 10

def snapshot():
    jobs = tg.run_jobs(RUN_ID)
    plan_done = any(j['name'] == 'plan' and j['status'] == 'completed' for j in jobs)
    total = done = 0
    for j in jobs:
        if j['name'].startswith('render'):
            for s in j.get('steps', []):
                if s['name'].startswith('Render chunk'):
                    total += 1; done += 1 if s['status'] == 'completed' else 0
    asm = [j for j in jobs if j['name'] == 'assemble']
    asm_pct = 0.0
    if asm:
        a = asm[0]
        if a['status'] == 'completed': asm_pct = 1.0
        elif a['status'] == 'in_progress':
            st = a.get('steps', []); asm_pct = 0.3 * (sum(1 for s in st if s['status'] == 'completed') / max(1, len(st)))
    pct = (W_PLAN if plan_done else 0) + (W_RENDER * done / total if total else 0) + W_ASM * asm_pct
    return pct, done, total, plan_done, asm

def main():
    t0 = time.time(); last = -10; announced_plan = False
    while True:
        try:
            pct, done, total, plan_done, asm = snapshot()
        except Exception as e:
            print('snapshot error', e); time.sleep(20); continue
        if asm and asm[0]['status'] == 'completed': break
        if plan_done and not announced_plan: announced_plan = True
        if pct - last >= 10 and pct < 98:
            last = int(pct // 10) * 10
            p = int(pct); elapsed = time.time() - t0
            eta = T.ETA.format(minutes=max(1, int(elapsed * (100 - pct) / max(pct, 1) / 60))) if pct >= 10 else ''
            stage = T.STAGE_ASSEMBLE if (total and done == total) else T.STAGE_RENDER.format(done=done, total=total) if total else '📋 Hazırlanıyor'
            tg.send(CHAT, T.PROGRESS.format(pct=p, left=100 - p, stage=stage, eta=eta))
        time.sleep(30)

if __name__ == '__main__': main()
