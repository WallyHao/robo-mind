#!/usr/bin/env bash
set -euo pipefail

echo "=== RoboMind dependency installer ==="
echo ""

# dimOS
echo "[1/4] dimOS"
DIMOS_DIR="${DIMOS_DIR:-$HOME/dimos}"
if [ ! -d "$DIMOS_DIR" ]; then
    git clone https://github.com/dimensionalOS/dimos.git "$DIMOS_DIR"
    pip install -e "$DIMOS_DIR"
else
    echo "  already exists at $DIMOS_DIR, skipping clone"
fi

# BEHAVIOR-1K
echo "[2/4] BEHAVIOR-1K"
BEHAVIOR_DIR="${BEHAVIOR_DIR:-$HOME/BEHAVIOR-1K}"
if [ ! -d "$BEHAVIOR_DIR" ]; then
    git clone https://github.com/StanfordVL/BEHAVIOR-1K.git "$BEHAVIOR_DIR"
    cd "$BEHAVIOR_DIR"
    git submodule update --init --recursive
    cd -
else
    echo "  already exists at $BEHAVIOR_DIR, skipping clone"
fi

# Python dependencies
echo "[3/4] Python packages"
pip install -e ".[dev]"

echo ""
echo "=== Done ==="
echo "Set BEHAVIOR_DIR and DIMOS_SITE_PATH in .env before running 'make run'"
