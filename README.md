# Roblox Story Video Factory

Telegram bot + GitHub Actions + Blender pipeline that turns a **story file** and a **voice recording** into a vertical
1080x1920, 60 fps, silent-picture-plus-voice-and-music Roblox-style video.

```
Claude chat ──► story file (.txt) + title + description
You ─────────► voice recording (MP3)
Telegram ────► send MP3, then reply to it with the story file
GitHub ──────► plan ─► 20 parallel Blender renders ─► assemble ─► video back to Telegram
```

* Picture is silent (no sound effects). Audio = your voice at 80 % + `assets/music/roblox-story-bg.mp3` at 20 %.
* A new camera angle every 1-2 seconds, locations/characters/props/faces are generated procedurally (Roblox look).
* Words named in the narration (cabinet, computer, dog ...) appear on screen. Subtitles are the **script words**,
  timed to your voice (speech recognition used only for timing), one word at a time, white, upper case, lower third.
* Languages: Turkish, English, Spanish, French, Arabic (`LANG:` header of the story file).
* The bot sends percentage progress messages and reminds you when the GitHub token (`TOKEN_EXPIRES`) is about to expire.

## Layout
| Path | Purpose |
|---|---|
| `.github/workflows/poll.yml` | Telegram listener (woken by cron-job.org) |
| `.github/workflows/render.yml` | plan -> parallel Blender shards -> assemble -> send |
| `bot/` | Telegram bot (poll, progress, finish, messages) |
| `engine/story.py` | story-file parser, shot planner, multilingual prop lexicon |
| `engine/align.py` | voice-to-script word timing |
| `engine/rbx/` | procedural Blender library: characters, faces, props, locations, camera |
| `engine/render_shard.py` | Blender entry point (renders one frame range) |
| `engine/post.py` | colour grade, captions, per-chunk video encoding |
| `engine/assemble.py` | joins parts, mixes audio, builds Telegram preview |
| `docs/STORY_FORMAT.md` | the story file format |
| `examples/demo_story_en.txt` | demo used by `/test` and `/testhd` |

## Secrets (Settings -> Secrets and variables -> Actions)
`TELEGRAM_BOT_TOKEN`, `ALLOWED_CHAT_ID`, `TOKEN_EXPIRES` (date the GitHub token expires, `YYYY-MM-DD`).

All rights reserved. See `LICENSE` and `NOTICE.md`.
