#!/bin/sh
# Launcher for voice.py: runs it with the studio's Python venv, from any project.
# Works through a symlink (~/.claude/skills/voice-text -> <studio>/.claude/skills/voice-text).
here=$(dirname "$(readlink -f "$0")")
studio=$(cd "$here/../../../.." && pwd)
py="$studio/.venv/bin/python"
if [ ! -x "$py" ]; then
  echo "voice: no Python venv at $py. Set it up with step 2 of $studio/site/starter/SETUP.md" >&2
  exit 1
fi
exec "$py" "$here/voice.py" "$@"
