#!/usr/bin/env sh
# Build the code-only zip the hackathon asks for (max 50 MB, no videos).
set -eu
cd "$(dirname "$0")/.."
rm -f submission.zip
git ls-files -z | xargs -0 zip -q submission.zip
if [ -d results ]; then zip -qr submission.zip results -x '*/__pycache__/*'; fi
ls -lh submission.zip
