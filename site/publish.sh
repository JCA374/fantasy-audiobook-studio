#!/usr/bin/env bash
# Publish the current state of the project to the website.
# usage: site/publish.sh "what changed"
set -euo pipefail
cd "$(dirname "$0")/.."
python3 .claude/skills/speech-flow/scripts/test_rules.py >/dev/null || { python3 .claude/skills/speech-flow/scripts/test_rules.py; echo "rule tests failed: not publishing"; exit 1; }
.venv/bin/python site/build.py --audio      # converts new training audio to mp3 and checks the build
git add -A
if git diff --cached --quiet; then echo "nothing to publish"; exit 0; fi
git commit -q -m "${1:-Update}"
git push -q
echo "pushed; GitHub Actions is rebuilding the site (about a minute)"
