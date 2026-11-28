import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tg, messages as T
kind = sys.argv[1]; chat = os.environ['CHAT_ID']
if kind == 'failed': tg.send(chat, T.FAILED.format(url=os.environ.get('RUN_URL', '')))
elif kind == 'plan': tg.send(chat, sys.argv[2])
