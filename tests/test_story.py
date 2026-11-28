"""Run: python3 tests/test_story.py   (no Blender needed)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine'))
import story as S

def test_parse():
    st = S.parse_story(open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'demo_story_en.txt')).read())
    assert st['lang'] == 'en' and len(st['shots']) >= 8 and 'Max' in st['cast']
    assert st['shots'][0]['chars'][0]['name'] == 'Max' and st['shots'][0]['chars'][0]['focus']

def test_lexicon():
    assert S.lexicon_kind(S.fold('dolabın')) == 'cabinet'
    assert S.lexicon_kind(S.fold('Bilgisayarı')) == 'computer'
    assert S.lexicon_kind(S.fold('armario')) == 'cabinet'
    assert S.lexicon_kind(S.fold('الخزانة')) == 'cabinet'
    assert S.lexicon_kind(S.fold('the')) is None

def test_plan():
    st = S.parse_story(open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'demo_story_en.txt')).read())
    n = sum(len(s['narr'].split()) for s in st['shots'])
    times = [(i * 0.4, i * 0.4 + 0.3) for i in range(n)]
    plan = S.build_plan(st, times, 60, 1080, 1920, 16)
    assert plan['shots'][0]['start_f'] == 0
    for a, b in zip(plan['shots'], plan['shots'][1:]): assert a['end_f'] == b['start_f']
    assert all((s['end_f'] - s['start_f']) / 60 <= 2.3 for s in plan['shots']), 'a camera angle lasts longer than ~2 s'
    assert len(plan['captions']) == n

if __name__ == '__main__':
    test_parse(); test_lexicon(); test_plan(); print('all tests passed')
